import unittest
import requests
import json
import random
import string
import os
import base64
import logging
from dotenv import load_dotenv



# Load environment variables from .env file
load_dotenv(override=True)

# Get AUTH_TOKEN and PROJECT_ID from environment variables
AUTH_TOKEN = os.getenv('AUTH_TOKEN')
PROJECT_ID = os.getenv('PROJECT_ID')
SPACE_NAME = os.getenv('SPACE_NAME')
DEBUG = os.getenv('DEBUG')

BASE_URL = f"https://{SPACE_NAME}.signalwire.com/api/fabric/resources/ai_agents"
AUTHORIZATION = f"Basic {base64.b64encode(f'{PROJECT_ID}:{AUTH_TOKEN}'.encode()).decode()}"

# Set up logging
log_level = logging.DEBUG if DEBUG == 'True' else logging.INFO
logging.basicConfig(level=log_level)

class TestAgentAPI(unittest.TestCase):

    def setUp(self):
        logging.debug("\033[32mSetting up the test by creating a new agent.\033[0m")
        random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        payload = {"name": f"TestAgent_{random_name}"}
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': AUTHORIZATION
        }
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f"\033[32mPayload for agent creation: {payload}\033[0m")
        response = requests.post(BASE_URL, headers=headers, json=payload)
        logging.info(f"\033[33mAgent creation response: {response.status_code}\033[0m")
        
        self.assertEqual(response.status_code, 201, "Failed to create agent")
        
        self.agent_id = response.json().get('id')
        self.assertIsNotNone(self.agent_id, "Agent ID not found in response")
        
        self.agent_url = f"{BASE_URL}/{self.agent_id}"
        logging.debug(f"Agent created with ID: {self.agent_id}")

    def test_add_and_delete_sections(self):
        logging.debug("\033[32mStarting test to add and delete sections.\033[0m")
        with open('agent.json', 'r') as file:
            agent_data = json.load(file)

        sections = ["prompt", "post_prompt", "params", "pronounce", "hints", "languages", "swaig"]

        for section in sections:
            with self.subTest(section=section):
                logging.debug(f"Testing section: {section}")
                section_data = agent_data['sections']['main'][0]['ai'].get(section)
                self.assertIsNotNone(section_data, f"Section {section} not found in agent.json")

                payload = {section: section_data}
                logging.debug(f"\033[32mAdding section {section}\033[0m")
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    logging.debug(f"\033[32mPayload for adding section {section}: {payload}\033[0m")

                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': AUTHORIZATION
                }
                response = requests.put(self.agent_url, headers=headers, json=payload)
                logging.info(f"\033[33mAdd section {section} response: {response.status_code}\033[0m")
                self.assertEqual(response.status_code, 200, f"Failed to add section {section}")

                response = requests.get(self.agent_url, headers=headers)
                logging.info(f"\033[33mGet agent after adding section {section} response: {response.status_code}\033[0m")
                self.assertEqual(response.status_code, 200, f"Failed to retrieve agent after adding section {section}")
                retrieved_data = response.json().get('ai_agent', {}).get(section)
                self.assertEqual(retrieved_data, section_data, f"Section {section} data does not match after addition")

                if isinstance(section_data, list):
                    delete_payload = {section: []}
                else:
                    delete_payload = {section: {}}
                logging.debug(f"\033[32mDeleting section {section}\033[0m")
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    logging.debug(f"\033[32mPayload for deleting section {section}: {delete_payload}\033[0m")

                response = requests.put(self.agent_url, headers=headers, json=delete_payload)
                logging.info(f"\033[33mDelete section {section} response: {response.status_code}\033[0m")
                self.assertEqual(response.status_code, 200, f"Failed to delete section {section}")

                response = requests.get(self.agent_url, headers=headers)
                logging.info(f"\033[33mGet agent after deleting section {section} response: {response.status_code}\033[0m")
                self.assertEqual(response.status_code, 200, f"Failed to retrieve agent after deleting section {section}")
                retrieved_data = response.json().get('ai_agent', {}).get(section)
                self.assertEqual(retrieved_data, delete_payload[section], f"Section {section} was not deleted properly")

    def tearDown(self):
        logging.debug("\033[32mTearing down the test by deleting the agent.\033[0m")
        headers = {
            'Authorization': AUTHORIZATION
        }
        response = requests.delete(self.agent_url, headers=headers)
        logging.info(f"\033[33mAgent deletion response: {response.status_code}\033[0m")
        self.assertEqual(response.status_code, 204, "Failed to delete agent")

if __name__ == '__main__':
    unittest.main()