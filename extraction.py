## In order to extract only the table elements I’ve written a helper function to do so:
import re
import json
from html import escape
from bs4 import BeautifulSoup
import pandas as pd
from IPython.display import display
from treelib import Node, Tree

element_tree = Tree()
extracted_elements = {}
extracted_elements_table = []


def extract_json_elements(input_filename):
  # Read the JSON file
  with open(input_filename, 'r') as file:
    data = json.load(file)
    # Iterate over the JSON data and extract required elements
    for entry in data:
      text = entry["text"]

      if "Table" == entry["type"]:
          text = entry["metadata"]["text_as_html"]

      if 'parent_id' in entry['metadata']:
        extracted_elements[entry["element_id"]] = {
          "_id": entry["element_id"],
          "filename":entry["metadata"]["filename"],
          "page_number":entry["metadata"]["page_number"],
          "parent_id":entry["metadata"]["parent_id"],
          "type":entry["type"],
          "text":text
          }
      else:
        extracted_elements[entry["element_id"]] = {
            "_id": entry["element_id"],
            "filename":entry["metadata"]["filename"],
            "page_number":entry["metadata"]["page_number"],
            "type":entry["type"],
            "text":text
            }

  # construct element dependency tree
  for k, element in extracted_elements.items():
      if "parent_id" in element:
        # print(element)
        parent_target = element["parent_id"]
        node = element_tree.get_node(parent_target)
        if node:
          element.pop("parent_id", None)
          element_tree.create_node(k, k, parent=parent_target, data = element)
        else:
          element.pop("parent_id", None)
          # element_parent = extracted_elements[parent_target].pop("parent_id", None)
          element_tree.create_node(parent_target, parent_target, parent="root", data = extracted_elements[parent_target])
          element_tree.create_node(k, k, parent=parent_target, data = element)

  return extracted_elements



def extract_json_table(input_filename):
  # Read the JSON file
  with open(input_filename, 'r') as file:
    data = json.load(file)
    # Iterate over the JSON data and extract required table elements
    for entry in data:
      if entry["type"] == "Table":
        entry["metadata"]["element_id"] = entry["element_id"]
        extracted_elements_table.append({"element_id":entry["element_id"], "metadata" : entry["metadata"]})

  return extracted_elements_table


#Define a function to clean table columns
def extract_table_from_html(table_html_string):
  # Rename the columns to be just the first element of each tuple
  # Function to convert elements to string
  def to_str(element):
      if isinstance(element, tuple):
          return '_'.join(map(str, element))  # Join tuple elements with an underscore
      else:
          return str(element)  # Convert integer to string

  # Find the table within the span element
  table = table_html_string.find('table')
  df_flattened = None
  if table:
      table_dfs = pd.read_html(table_html_string) # Get the first DataFrame
      table_df = table_dfs[0] # assume only one table per json tab
      df_flattened = table_df.applymap(str)  # Convert all values to string
      df_flattened.columns = [to_str(col) for col in df_flattened.columns] # Column headers parsed as set by pdf extractor, force to string for compatibility

  return df_flattened


# Define a fuctnion to formatn tables cells
def format_table(df_table):
    # df_table =  pd.DataFrame(ds_table)
    df_numeric = df_table.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
    df_combined = pd.concat([df_table.iloc[:, 0], df_numeric], axis=1)
    df_cleaned = df_combined.dropna(how='any')
    return df_cleaned


# Define a function to clean the data
def clean_text(text):

    # Function to convert matched text to negative number
    def make_negative(match):
        number = match.group(1).replace(',', '')
        return f"{-int(number)}"

    # Check if the text is a string
    if isinstance(text, str):
        # Replace unwanted characters if it's a string
        text = text.replace('#', '').replace('*', '')


        # Regular expression to match numbers in parentheses with commas
        pattern = r'\((\d{1,3}(,\d{3})*)\)'
        # Replace all occurrences of the pattern with its negative equivalent
        text = re.sub(pattern, make_negative, text)

        # Check if the text is a number with commas
        if re.match(r'^-?\d{1,3}(,\d{3})*\.\d+$', text):
            # Remove commas and convert to float
            return float(text.replace(',', ''))
        # Check if the text is an integer with commas
        elif re.match(r'^-?\d{1,3}(,\d{3})*$', text):
            # Remove commas and convert to integer
            return int(text.replace(',', ''))
    # Return the text as is if it's not a string
    return text


# Define a function to clean the data
def parse_html_table(data_tables):

  # Initialize an empty dictionary to hold the tables with span_id as the key
  # and the table data as the value
  tables_dict = {}


  # Find all span elements with an 'id' attribute
  for data_table in data_tables:
      span_id = data_table['element_id']

      # Initialize a dictionary to hold the metadata and table data for the current span
      span_data = {}

      # Extract the 'metadata' attribute if it exists
      metadata = data_table.get('metadata', None)

      if metadata:
          span_data['metadata'] = metadata

      # Find the table within the span element
      table = data_table.get('text_as_html', None)
      if table:
          # Use pandas to read the table
          table_df = pd.read_html(str(table)) # Get the first DataFrame
          span_data['table'] = table_df

      # Add the span data to the main dictionary using the span_id as the key
      tables_dict[span_id] = span_data


  datasets = []

  # Get the first key-value pair based on insertion order
  for span_id, span_data in tables_dict.items():
      # Access the metadata and the table DataFrame
      metadata = span_data.get('metadata')
      table_html = metadata.get('text_as_html')
      df_table = extract_table_from_html(table_html)
      df_table_clean = df_table.applymap(clean_text)
      datasets.append({
          "_id": span_id,  # Corrected the syntax for dictionary keys (no quotes)
          "meta": metadata,  # Corrected the variable name ('metadata' instead of 'metdata')
          "data": df_table_clean.to_dict("records"),  # Assuming you want to store the first DataFrame in the list
          "data_raw": df_table.to_dict("records")  # raw data format, without formatting
          })

  return datasets


def process_extraction(filePath):
  element_tree.create_node("root", "root")
  data_elements = extract_json_elements(filePath)
  data_tables = extract_json_table(filePath)
  return parse_html_table(data_tables)



file_path="/content/files/downloaded_file.pdf.json"
db = client['db_finance_report']
collection = db['collection_tencent']
collection.drop()
insert_collection = process_extraction(file_path)
collection.insert_many(insert_collection);
print(f'Written {collection.count_documents({})} tables documents into mongodb collection_tencent.')

extracted_elements_val=[]
for k, v in extracted_elements.items():
  extracted_elements_val.append(v)

collection = db['collection_tencent_notes']
collection.drop()
collection.insert_many(extracted_elements_val);
print(f'Written {collection.count_documents({})} element documents into mongodb collection_tencent_notes.')


print(f'Element Tree size is {element_tree.size()}.')
