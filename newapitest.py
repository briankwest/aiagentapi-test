import unittest
import requests
import json
import random
import string
import os
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

# Get AUTH_TOKEN and PROJECT_ID from environment variables
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
PROJECT_ID = os.getenv('PROJECT_ID')
SPACE_NAME = os.getenv('SPACE_NAME')

# Define the API endpoint and authorization details
BASE_URL = f"https://{SPACE_NAME}.signalwire.com/api/fabric/resources/ai_agents"
AUTHORIZATION = f"Basic {base64.b64encode(f'{PROJECT_ID}:{AUTH_TOKEN}'.encode()).decode()}"

class TestAgentAPI(unittest.TestCase):

    def setUp(self):
        # Generate a random name for the agent
        random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        payload = {"name": f"TestAgent_{random_name}"}
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': AUTHORIZATION
        }
        response = requests.post(BASE_URL, headers=headers, json=payload)
        
        # Check if the agent was created successfully
        self.assertEqual(response.status_code, 201, "Failed to create agent")
        
        # Retrieve the agent ID from the response
        self.agent_id = response.json().get('id')
        self.assertIsNotNone(self.agent_id, "Agent ID not found in response")
        
        # Construct the agent URL using the retrieved agent ID
        self.agent_url = f"{BASE_URL}/{self.agent_id}"

    def test_add_and_delete_sections(self):
        # Load the agent.json file
        with open('agent.json', 'r') as file:
            agent_data = json.load(file)

        # Define the sections to be tested
        sections = ["prompt", "post_prompt", "params", "pronounce", "hints", "languages", "swaig"]

        for section in sections:
            with self.subTest(section=section):
                section_data = agent_data['sections']['main'][0]['ai'].get(section)
                self.assertIsNotNone(section_data, f"Section {section} not found in agent.json")

                # Prepare the payload
                payload = {section: section_data}

                # Send PUT request to add the section
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': AUTHORIZATION
                }
                response = requests.put(self.agent_url, headers=headers, json=payload)
                self.assertEqual(response.status_code, 200, f"Failed to add section {section}")

                # Perform a GET request to verify the section was added
                response = requests.get(self.agent_url, headers=headers)
                self.assertEqual(response.status_code, 200, f"Failed to retrieve agent after adding section {section}")
                retrieved_data = response.json().get('ai_agent', {}).get(section)
                self.assertEqual(retrieved_data, section_data, f"Section {section} data does not match after addition")

                # Prepare payload for deleting the section
                if isinstance(section_data, list):
                    delete_payload = {section: []}
                else:
                    delete_payload = {section: {}}

                # Send PUT request to delete the section
                response = requests.put(self.agent_url, headers=headers, json=delete_payload)
                self.assertEqual(response.status_code, 200, f"Failed to delete section {section}")

                # Perform a GET request to verify the section was deleted
                response = requests.get(self.agent_url, headers=headers)
                self.assertEqual(response.status_code, 200, f"Failed to retrieve agent after deleting section {section}")
                retrieved_data = response.json().get('ai_agent', {}).get(section)
                self.assertEqual(retrieved_data, delete_payload[section], f"Section {section} was not deleted properly")

    def tearDown(self):
        # Clean up by deleting the agent
        headers = {
            'Authorization': AUTHORIZATION
        }
        response = requests.delete(self.agent_url, headers=headers)
        self.assertEqual(response.status_code, 204, "Failed to delete agent")

if __name__ == '__main__':
    unittest.main()