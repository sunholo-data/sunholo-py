import os
import base64
import json
from datetime import datetime
import urllib.parse

from ..logging import log

from ..utils.parsers import get_clean_website_name

class BrowseWebWithImagePromptsBot:
    """
    BrowseWebWithImagePromptsBot is a base class for creating bots that interact with web pages using Playwright.
    The bot can perform actions such as navigating, clicking, scrolling, typing text, and taking screenshots.
    It also supports cookie management to maintain session state across interactions.

    Methods:
    - __init__(session_id, website_name, browser_type='chromium', headless=True):
        Initializes the bot with the given session ID, website name, browser type, and headless mode.
        Supported browser types: 'chromium', 'firefox', 'webkit'.

    - load_cookies():
        Loads cookies from a file and adds them to the browser context.

    - save_cookies():
        Saves the current cookies to a file.

    - navigate(url):
        Navigates to the specified URL.

    - click(selector):
        Clicks on the element specified by the selector.

    - scroll(direction='down', amount=1):
        Scrolls the page in the specified direction ('down', 'up', 'left', 'right') by the specified amount.

    - type_text(selector, text):
        Types the specified text into the element specified by the selector.

    - take_screenshot():
        Takes a screenshot and saves it with a timestamp in the session-specific directory. Returns the path to the screenshot.

    - get_latest_screenshot_path():
        Retrieves the path to the most recent screenshot in the session-specific directory.

    - create_prompt_vars(current_action_description, session_goal):
        Creates a dictionary of prompt variables from the current action description and session goal.

    - send_screenshot_to_llm(screenshot_path, current_action_description="", session_goal=""):
        Encodes the screenshot in base64, creates prompt variables, and sends them to the LLM. Returns the new instructions from the LLM.

    - send_prompt_to_llm(prompt_vars, screenshot_base64):
        Abstract method to be implemented by subclasses. Sends the prompt variables and screenshot to the LLM and returns the response.

    - close():
        Saves cookies, closes the browser, and stops Playwright.

    - execute_instructions(instructions):
        Executes the given set of instructions, takes a screenshot after each step, and sends the screenshot to the LLM for further instructions.

    Example usage:

    ```python
    class ProductionBot(BrowseWebWithImagePromptsBot):
        def send_prompt_to_llm(self, prompt_vars, screenshot_base64):
            # Implement the actual logic to send the prompt and screenshot to the LLM and return the response
            api_url = "https://api.example.com/process"  # Replace with the actual LLM API endpoint
            headers = {"Content-Type": "application/json"}
            data = {
                "prompt": prompt_vars,
                "screenshot": screenshot_base64
            }
            response = requests.post(api_url, headers=headers, data=json.dumps(data))
            return response.text  # Assuming the response is in JSON format

    @app.route('/run-bot', methods=['POST'])
    def run_bot():
        data = request.json
        session_id = data.get('session_id')
        website_name = data.get('website_name')
        browser_type = data.get('browser_type', 'chromium')
        current_action_description = data.get('current_action_description', "")
        session_goal = data.get('session_goal', "")
        
        bot = ProductionBot(session_id=session_id, website_name=website_name, browser_type=browser_type, headless=True)
        
        # Check if initial instructions are provided
        initial_instructions = data.get('instructions')
        if initial_instructions:
            bot.execute_instructions(initial_instructions)
        else:
            bot.execute_instructions([{'action':'navigate', 'url': website_name}])
        
        # Take initial screenshot and send to LLM
        screenshot_path = bot.take_screenshot()
        new_instructions = bot.send_screenshot_to_llm(screenshot_path, current_action_description, session_goal)
        bot.execute_instructions(new_instructions)
        
        # Take final screenshot
        bot.take_screenshot()
        
        bot.close()
        
        return jsonify({"status": "completed", "new_instructions": new_instructions})

    if __name__ == "__main__":
        app.run(host='0.0.0.0', port=8080)
    ```
    """
#class BrowseWebWithImagePromptsBot:
    def __init__(self, session_id, website_name, browser_type='chromium', headless=True, max_steps=10):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as err:
            print(err)
            sync_playwright = None
        if not sync_playwright:
            raise ImportError("playright needed for BrowseWebWithImagePromptsBot class - install via `pip install sunholo[tools]`")
        self.session_id = session_id or datetime.now().strftime("%Y%m%d%H%M%S")
        self.website_name = website_name
        self.browser_type = browser_type
        self.max_steps = max_steps
        self.steps = 0
        self.screenshot_dir = f"browser_tool/{get_clean_website_name(website_name)}/{session_id}"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.cookie_file = os.path.join(self.screenshot_dir, "cookies.json")
        self.playwright = sync_playwright().start()
        
        if browser_type == 'chromium':
            self.browser = self.playwright.chromium.launch(headless=headless)
        elif browser_type == 'firefox':
            self.browser = self.playwright.firefox.launch(headless=headless)
        elif browser_type == 'webkit':
            self.browser = self.playwright.webkit.launch(headless=headless)
        else:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.load_cookies()
        self.actions_log = []
        self.session_goal = None
        self.session_screenshots = []

    def load_cookies(self):
        if os.path.exists(self.cookie_file):
            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
                self.context.add_cookies(cookies)

    def save_cookies(self):
        cookies = self.context.cookies()
        with open(self.cookie_file, 'w') as f:
            json.dump(cookies, f)

    def navigate(self, url):
        try:
            self.page.goto(url)
            self.page.wait_for_load_state()
            log.info(f'Navigated to {url}')
            self.actions_log.append(f"Navigated to {url}")
        except Exception as err:
            log.warning(f"navigate failed with {str(err)}")
            self.actions_log.append(f"Tried to navigate to {url} but got an error")


    def click(self, selector):
        try:
            self.page.click(selector)
            self.page.wait_for_load_state()
            log.info(f"Clicked on element with selector {selector}")
            self.actions_log.append(f"Clicked on element with selector {selector}")
        except Exception as err:
            log.warning(f"click failed with {str(err)}")
            self.actions_log.append(f"Tried to click on element with selector {selector} but got an error")            

    def scroll(self, direction='down', amount=1):
        try:
            for _ in range(amount):
                if direction == 'down':
                    self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                elif direction == 'up':
                    self.page.evaluate("window.scrollBy(0, -window.innerHeight)")
                elif direction == 'left':
                    self.page.evaluate("window.scrollBy(-window.innerWidth, 0)")
                elif direction == 'right':
                    self.page.evaluate("window.scrollBy(window.innerWidth, 0)")
                self.page.wait_for_timeout(500)
                log.info(f"Scrolled {direction} by {amount} page heights")
                self.actions_log.append(f"Scrolled {direction} by {amount} page heights")
        except Exception as err:
            log.warning(f"Scrolled failed with {str(err)}")
            self.actions_log.append(f"Tried to scroll {direction} by {amount} page heights but got an error")


    def type_text(self, selector, text):
        try:
            self.page.fill(selector, text)
            self.page.wait_for_load_state()
            log.info(f"Typed text '{text}' into element with selector {selector}")
            self.actions_log.append(f"Typed text '{text}' into element with selector {selector}")
        except Exception as err:
            log.warning(f"Typed text failed with {str(err)}")
            self.actions_log.append(f"Tried to type text '{text}' into element with selector {selector} but got an error")

    def take_screenshot(self, final=False):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        parsed_url = urllib.parse.urlparse({self.page.url})
        url_path = parsed_url.path
        if final:
            screenshot_path = os.path.join(self.screenshot_dir, f"final/{timestamp}_{url_path}.png")
        else:
            screenshot_path = os.path.join(self.screenshot_dir, f"{timestamp}_{url_path}.png")
        self.page.screenshot(path=screenshot_path)
        log.info(f"Screenshot {self.page.url} taken and saved to {screenshot_path}")
        #self.actions_log.append(f"Screenshot {self.page.url} taken and saved to {screenshot_path}")
        self.session_screenshots.append(screenshot_path)

        return screenshot_path

    def get_latest_screenshot_path(self):
        screenshots = sorted(
            [f for f in os.listdir(self.screenshot_dir) if f.startswith('screenshot_')],
            key=lambda x: os.path.getmtime(os.path.join(self.screenshot_dir, x)),
            reverse=True
        )
        if screenshots:
            return os.path.join(self.screenshot_dir, screenshots[0])
        return None

    def create_prompt_vars(self, last_message):
        prompt = {
            "last_actions": self.actions_log,
            "session_goal": self.session_goal,
            "last_message": last_message
        }
        return prompt
    
    def check_llm_response(self, response):
        if isinstance(response, dict):
            output = response
        elif isinstance(response, str):
            output = json.loads(response)

        #TODO: more validation
        log.info(f'Response: {output=}')

        if 'status' not in output:
            log.error(f'Response did not contain status')

        if 'new_instructions' not in output:
            log.warning(f'Response did not include new_instructions')
        
        if 'message' not in output:
            log.warning(f'Response did not include message')

        return output        

    def send_screenshot_to_llm(self, screenshot_path, last_message):
        with open(screenshot_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        prompt_vars = self.create_prompt_vars(last_message)
        response = self.send_prompt_to_llm(prompt_vars, encoded_image)  # Sending prompt and image separately
        
        return self.check_llm_response(response)

    def send_prompt_to_llm(self, prompt_vars, screenshot_base64):
        raise NotImplementedError("""
This method should be implemented by subclasses: `def send_prompt_to_llm(self, prompt_vars, screenshot_base64)`")
        prompt = {
            "last_actions": self.action_log,
            "session_goal": self.session_goal,
        }
""")

    def close(self):
        self.save_cookies()
        self.browser.close()
        self.playwright.stop()

    def execute_instructions(self, instructions: list, last_message: str=None):
        if not instructions: 
            log.info("No instructions found, returning immediately")
            return
        
        if self.steps >= self.max_steps:
            log.warning(f"Reached the maximum number of steps: {self.max_steps}")
            return
        
        if not isinstance(instructions, list):
            log.error(f"{instructions} {type(instructions)}")
        for instruction in instructions:
            if not isinstance(instruction, dict):
                log.error(f"{instruction} {type(instruction)}")
            action = instruction['action']
            if action == 'navigate':
                self.navigate(instruction['url'])
            elif action == 'click':
                self.click(instruction['selector'])
            elif action == 'scroll':
                self.scroll(instruction.get('direction', 'down'), instruction.get('amount', 1))
            elif action == 'type':
                self.type_text(instruction['selector'], instruction['text'])
            self.steps += 1
            if self.steps >= self.max_steps:
                log.warning(f"Reached the maximum number of steps: {self.max_steps}")
                return
            
        screenshot_path = self.take_screenshot()
        next_browser_instructions = self.send_screenshot_to_llm(
                screenshot_path, 
                last_message=last_message)
            
        return next_browser_instructions
    
    def start_session(self, instructions, session_goal):
            self.session_goal = session_goal

            if not instructions:
                instructions = [{'action': 'navigate', 'url': self.website_name}]

            next_instructions = self.execute_instructions(instructions)

            in_session = True
            while in_session:
                if next_instructions and 'status' in next_instructions:
                    if next_instructions['status'] == 'in-progress':
                        log.info(f'Browser message: {next_instructions.get('message')}')
                        if 'new_instructions' not in next_instructions:
                            log.error('Browser status: "in-progress" but no new_instructions')
                        last_message = next_instructions['message']
                        log.info(f'Browser message: {last_message}')
                        next_instructions = self.execute_instructions(next_instructions['new_instructions'], last_message=last_message)
                    else:
                        log.info(f'Session finished due to status={next_instructions["status"]}')
                        in_session=False
                        break
                else:
                    log.info('Session finished due to next_instructions being empty')
                    in_session=False
                    break
            
            log.info("Session finished")
            final_path = self.take_screenshot(final=True)
            self.close()
            
            return {
                "website": self.website_name,
                "log": self.actions_log,
                "next_instructions": next_instructions,
                "session_screenshots": self.session_screenshots,
                "final_page": final_path,
            }

