from makersite_ml.query_utils import query_to_dataframe
from textwrap import dedent
import pandas as pd 
import json

category_tech_specs_dict = pd.read_pickle('category_technical_specs_above_threshold.pkl')
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

import json
import ast

from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from typing import Dict, List, Any

app = FastAPI()

# Define the error messages
ERROR_CATEGORY_NOT_FOUND = "Category name not found in the dictionary."
ERROR_INTERNAL_SERVER = "Internal server error occurred."

@app.post("/get_closest_matches")
async def get_closest_matches_endpoint(item_dict: Dict[str, Any]) -> List[Dict[str, Any]]:

    try:
        closest_matches = get_closest_matches(item_dict)
        return closest_matches
    except KeyError:
        raise HTTPException(status_code=404, detail=ERROR_CATEGORY_NOT_FOUND)
    except Exception as e:
        print("Internal server error:", e)  # Log the error for debugging purposes
        raise HTTPException(status_code=500, detail=ERROR_INTERNAL_SERVER)

def get_closest_matches(data: Dict[str, Any]) -> List[Dict[str, Any]]:

    bom_mpn = data.get('mpn', None)
    category_name = data.get('category_names', None)
    new_component_specs = data.get('technicalData', None)
   
    def convert_to_tuple(category_string):
        cleaned_string = category_string.strip('{}')
        words = cleaned_string.split(', ')
        formatted_words = [word.strip() for word in words]
        result_tuple = tuple(formatted_words)
        return result_tuple

    category_tuple = convert_to_tuple(category_name)

    numerical_specs_present = []
    categorical_specs_present = []

    if category_tuple in category_tech_specs_dict:
        numerical_specs_dict = category_tech_specs_dict[category_tuple].get('numerical', [])
        categorical_specs_dict = category_tech_specs_dict[category_tuple].get('categorical', [])
        
        for spec in new_component_specs:
            key = spec['key']
            value = spec['value']
            
            is_numerical = False
            try:
                float(value)  # Try converting the value to a float
                is_numerical = True
            except ValueError:
                pass
            
            if key in numerical_specs_dict and is_numerical:
                numerical_specs_present.append(spec)
            elif key in categorical_specs_dict and not is_numerical:
                categorical_specs_present.append(spec)
    else:
        raise KeyError(ERROR_CATEGORY_NOT_FOUND)
    
    closest_matches = compare_specs(category_name, numerical_specs_present, categorical_specs_present)
    return closest_matches


def compare_specs(category_name, numerical_specs_present, categorical_specs_present, tolerance=20):
    query = f'''
        SELECT
            t.mpn,
            t.sourcengine_details,
            c.sourcengine_category_names,
            s.substance_names,
            s.amount
        FROM
            makersite.technical_specifications_data t
        JOIN
            makersite.part_category_lookup c ON t.mpn = c.mpn
        JOIN
            makersite.substance_summaries_of_full_material_declarations s ON (
                REPLACE(c.manufacturer, ' ', '_') || '/' || REPLACE(c.mpn, '/', '%2F') || '.xml') = s.source_file
        WHERE
            c.sourcengine_category_names = '{category_name}'
            AND s.amount > 0 AND s.amount <= 1;
    '''

    df = query_to_dataframe(query)

    df['substance_names'] = df['substance_names'].apply(lambda x: tuple(x) if x is not None else None)
    df['sourcengine_category_names'] = df['sourcengine_category_names'].apply(lambda x: tuple(x) if x is not None else None)
    df = df.drop_duplicates(subset=['mpn','substance_names','amount'], keep='first')

    match_results = []
    matched_mpns = set()  # Set to keep track of matched MPNs

    # Function to calculate the range and check for matches
    def is_within_range(new_value, old_value, tolerance):
        try:
            new_value = float(new_value)
            old_value = float(old_value)
            tolerance_factor = tolerance / 100
            lower_bound = new_value * (1 - tolerance_factor)
            upper_bound = new_value * (1 + tolerance_factor)
            return lower_bound <= old_value <= upper_bound
        except ValueError:
            return False  # If values are not numbers, return False

    # Iterate through each row in the DataFrame
    for index, row in df.iterrows():
        mpn = row['mpn']  # Assuming 'mpn' is the column name for Manufacturer Part Number

        # Skip the MPN if it has already been matched
        if mpn in matched_mpns:
            continue

        numerical_matches = 0
        categorical_matches = 0
        matched_numerical_specs = []  # List to store matched numerical specifications
        matched_categorical_specs = []  # List to store matched categorical specifications
        unmatched_numerical_specs = []  # List to store unmatched numerical specifications
        unmatched_categorical_specs = []  # List to store unmatched categorical specifications

        # Convert the list of dictionaries to a single dictionary for old_comp
        old_comp_specs = row['sourcengine_details']
        old_comp = {spec['key']: spec for spec in old_comp_specs if 'key' in spec}

        # Function to compare and record matches
        def compare_and_record_matches(spec_list, match_counter, matched_specs, unmatched_specs, is_numerical=False):
            for new_spec in spec_list:
                if new_spec['key'] in old_comp:
                    old_spec = old_comp[new_spec['key']]
                    if 'value' in new_spec and 'value' in old_spec:
                        match_found = False
                        if is_numerical:
                            match_found = is_within_range(new_spec['value'], old_spec['value'], tolerance)
                        else:
                            match_found = str(new_spec['value']) == str(old_spec['value'])
                        if match_found:
                            match_counter += 1
                            matched_specs.append(old_spec)
                        else:
                            unmatched_specs.append(new_spec)
                    else:
                        unmatched_specs.append(new_spec)
            return match_counter

        # Compare specifications and record matches
        numerical_matches = compare_and_record_matches(numerical_specs_present, numerical_matches,
                                                       matched_numerical_specs, unmatched_numerical_specs,
                                                       is_numerical=True)
        categorical_matches = compare_and_record_matches(categorical_specs_present, categorical_matches,
                                                         matched_categorical_specs, unmatched_categorical_specs)

        # Store the total matches and matched specifications
        total_matches = numerical_matches + categorical_matches
        if total_matches > 0:  # Only store results if there are matches
            match_results.append((mpn, total_matches, matched_numerical_specs, matched_categorical_specs,
                                  unmatched_numerical_specs, unmatched_categorical_specs))
            matched_mpns.add(mpn)  # Add the matched MPN to the set

    # Get the top 5 rows with the highest scores
    top_5_matches = sorted(match_results, key=lambda x: x[1], reverse=True)[:5]

    # Prepare results for display
    closest_matches = []
    for mpn, count, num_specs, cat_specs, unmatched_num_specs, unmatched_cat_specs in top_5_matches:
        match_info = {"MPN": mpn, "Matches": count, "Matched Numerical Specs": num_specs,
                      "Matched Categorical Specs": cat_specs, "Unmatched Numerical Specs": unmatched_num_specs,
                      "Unmatched Categorical Specs": unmatched_cat_specs}
        closest_matches.append(match_info)

    return closest_matches



@app.post("/get_closest_matches")
async def get_closest_matches_endpoint(item_dict: Dict[str, Any]) -> List[Dict[str, Any]]:

    
    
    item_json = json.dumps(item_dict)
    item_single_quoted = item_json.replace('"', "'")
    data_str = item_single_quoted.strip('"')
    data_dict = ast.literal_eval(data_str)

    closest_matches = get_closest_matches(data_dict)
    return closest_matches
   







