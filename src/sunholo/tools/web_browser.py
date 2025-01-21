import os
import base64
import json
from datetime import datetime
import urllib.parse
import time
from io import BytesIO

from ..custom_logging import log

from ..utils.parsers import get_clean_website_name

try:
    from playwright.sync_api import sync_playwright, Response
except ImportError:
    sync_playwright = None
    Response = None

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
    def __init__(
            self,
            website_name:str, 
            session_id: str=None, 
            browser_type:str='chromium', 
            headless:bool=True, 
            max_steps:int=10
        ):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as err:
            print(err)
            sync_playwright = None

        if not sync_playwright:
            raise ImportError("playright needed for BrowseWebWithImagePromptsBot class - install via `pip install sunholo[tools]`")
        
        log.info(f"Starting BrowseWebWithImagePromptsBot with {website_name=}, {session_id=}, {browser_type=}, {headless=}, {max_steps=}")
        
        # Assign session_id if it is None or 'None'
        if not session_id or session_id == 'None':
            self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        else:
            self.session_id = session_id

        self.website_name = website_name
        self.browser_type = browser_type or 'chromium'
        self.max_steps = int(max_steps)
        self.steps = 0
        self.screenshot_dir = f"browser_tool/{get_clean_website_name(website_name)}/{self.session_id}"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.cookie_file = os.path.join(self.screenshot_dir, "cookies.json")
        self.action_log_file = os.path.join(self.screenshot_dir, "action_log.json")
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
        self.action_log = []
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
    
    def save_action_log(self):
        with open(self.action_log_file, 'w') as f:
            json.dump(self.action_log, f)
    
    def load_action_log(self):
        if os.path.exists(self.action_log_file):
            with open(self.action_log_file, 'r') as f:
                action_log = json.load(f)
                self.action_log = action_log

    def navigate(self, url):
        def handle_response(response: Response): # type: ignore
                status = response.status
                url = response.url
                if 300 <= status < 400:
                    log.info(f"Redirecting from {url}")
        try:
            self.page.on("response", handle_response)

            previous_url = self.page.url

            response = self.page.goto(url)
            status = response.status
            if status != 200:
                log.error(f"Failed to navigate to {url}: HTTP {status}")
                self.action_log.append(f"Tried to navigate to {url} but failed: HTTP {status} - browsing back to {previous_url}")
                self.page.go_back()
  
            self.page.wait_for_load_state()
            log.info(f'Navigated to {self.page.url}')
            self.action_log.append(f"Navigated to {self.page.url}")

        except Exception as err:
            log.warning(f"navigate failed with {str(err)}")
            self.action_log.append(f"Tried to navigate to {url} but got an error")

    def get_locator_via_roles_and_placeholder(self, selector: str):
        interactive_roles = ["button", "link", "menuitem", "menuitemcheckbox", "menuitemradio", "tab", "option"]

        for role in interactive_roles:
            log.info(f'Trying role {role} for selector {selector}')
            elements = self.page.get_by_role(role).get_by_placeholder(selector).locator("visible=true").all()
            if elements:
                log.info(f"Got {len(elements)} elements for selector {selector} with role {role}")
                for element in elements:
                    try:
                        log.info(f"Trying {selector} with element.hover locator: {element}")
                        try:
                            element.hover(timeout=10000, trial=True)
                            self.action_log.append(f"Successfully found element via selector: {selector}")

                            return element
                        
                        except Exception as err:
                            log.warning(f"Could not hover over element: {element} {str(err)} - trying next element")
                    except Exception as e:
                        log.error(f"Failed to get locator for selector '{selector}' with role {role}: {str(e)}")
                    
                    time.sleep(0.5)  # Wait for a bit before retrying
            
            log.info(f"No elements for '{selector}' within role '{role}'")

        self.action_log.append(f"FAILED: Using page.get_by_role('role').get_by_placeholder('{selector}').locator('visible=true') could not find any valid element. Try something else.")
        return None
    
    def get_locator_via_roles_and_text(self, selector: str):
        interactive_roles = ["button", "link", "menuitem", "menuitemcheckbox", "menuitemradio", "tab", "option"]

        for role in interactive_roles:
            log.info(f'Trying role {role} for selector {selector}')
            elements = self.page.get_by_role(role).get_by_text(selector).locator("visible=true").all()
            if elements:
                log.info(f"Got {len(elements)} elements for selector {selector} with role {role}")
                for element in elements:
                    try:
                        log.info(f"Trying {selector} with element.hover locator: {element}")
                        try:
                            element.hover(timeout=10000, trial=True)
                            self.action_log.append(f"Successfully found element via selector: {selector}")

                            return element
                        
                        except Exception as err:
                            log.warning(f"Could not hover over element: {element} {str(err)} - trying next element")
                    except Exception as e:
                        log.error(f"Failed to get locator for selector '{selector}' with role {role}: {str(e)}")
                    
                    time.sleep(0.5)  # Wait for a bit before retrying
            
            log.info(f"No elements for '{selector}' within role '{role}'")

        self.action_log.append(f"FAILED: Using page.get_by_role('role').get_by_text('{selector}').locator('visible=true') could not find any valid element. Try something else.")
        return None

    def get_locator(self, selector, by_text=True):
        if by_text:
            element = self.get_locator_via_roles_and_text(selector)
        else:
            element = self.page.locator(selector)
        
        if element:
            return element

        log.error(f"Failed to get locator for selector {selector}")

        return None

    def click(self, selector):
        (x,y)=(0,0)

        element = self.get_locator_via_roles_and_text(selector)
        if element is None:
            self.action_log.append(f"Tried to click on text {selector} but it was not a valid location to click")
            return (x,y)

        try:
            bounding_box = element.bounding_box()
            if bounding_box:
                x = bounding_box['x'] + bounding_box['width'] / 2
                y = bounding_box['y'] + bounding_box['height'] / 2
        except Exception as err:
            log.warning(f"Could not do bounding box - {str(err)}")
        
        try:
            element.click()
            self.page.wait_for_load_state()
            log.info(f"Clicked on {element=} with {selector=} at {x=},{y=}")
            self.action_log.append(f"Clicked on {element=} with {selector=} at {x=},{y=}")

            return (x,y)
        
        except Exception as err:
            log.warning(f"click failed with {str(err)}")
            self.action_log.append(f"Tried to click on {element=} with {selector=} at {x=},{y=} but got an error")  

            return (x,y)          

    def scroll(self, direction='down', amount=100):
        try:
            if direction == 'down':
                self.page.mouse.wheel(0, amount)
            elif direction == 'up':
                self.page.mouse.wheel(0, -amount)
            elif direction == 'left':
                self.page.mouse.wheel(-amount, 0)
            elif direction == 'right':
                self.page.mouse.wheel(amount, 0)
            self.page.wait_for_timeout(500)
            log.info(f"Scrolled {direction} by {amount} pixels")
            self.action_log.append(f"Scrolled {direction} by {amount} pixels")
        except Exception as err:
            log.warning(f"Scrolled failed with {str(err)}")
            self.action_log.append(f"Tried to scroll {direction} by {amount} pixels but got an error")

    def type_text(self, selector, text):
        (x,y)=(0,0)
        element = self.get_locator_via_roles_and_placeholder(selector)
        if element is None:
            self.action_log.append(f"Tried to type {text} via website text: {selector} but it was not a valid element to add text")
            return (x,y)

        try:
            bounding_box = element.bounding_box()
            if bounding_box:
                x = bounding_box['x'] + bounding_box['width'] / 2
                y = bounding_box['y'] + bounding_box['height'] / 2
        except Exception as err:
            log.warning(f"Could not do bounding box - {str(err)}")
        
        try:
            element.fill(text)
            self.page.wait_for_load_state()
            log.info(f"Typed text '{text}' into {element=} with {selector=} at {x=},{y=}")
            self.action_log.append(f"Typed text '{text}' into {element=} with {selector=} at {x=},{y=}")

            return (x, y)
        
        except Exception as err:
            log.warning(f"Typed text failed with {str(err)}")
            self.action_log.append(f"Tried to type text '{text}' into {element=} with {selector=} at {x=},{y=} but got an error")

            return (x, y)

    def execute_custom_command(self, command):
        """
        Executes a custom command on the page object.

        Args:
            command (str): The command string to be executed.
        """
        try:
            element_part = command.get('get_locator')
            operation = command.get('operation')

            if not element_part or not operation:
                raise ValueError("Both 'element_part' and 'operation' must be provided in the command")
            
            # Dynamically get the method and its parameters
            method_name, params = self.parse_element_part(element_part)
            method = getattr(self.page, method_name)
            element = method(*params)

            if not element:
                raise ValueError(f"Element not found for selector: {element_part}")

            # Execute the operation
            exec(f"element.{operation}")

            # Mark the action on the screenshot
            bounding_box = element.bounding_box()
            if bounding_box:
                x = bounding_box['x'] + bounding_box['width'] / 2
                y = bounding_box['y'] + bounding_box['height'] / 2
                mark_action = {'type': operation, 'position': (x, y)}
                self.take_screenshot(mark_action=mark_action)
            else:
                self.take_screenshot()

            log.info(f"Executed custom command on element: {element_part} with operation: {operation}")
            self.action_log.append(f"Executed custom command on element: {element_part} with operation: {operation}")

        except Exception as e:
            log.error(f"Failed to execute custom command: {command}. Error: {str(e)}")
            self.action_log.append(f"Failed to execute custom command: {command}. Error: {str(e)}")

    def parse_element_part(self, element_part):
        """
        Parses the element_part string to extract the method name and its parameters.

        Args:
            element_part (str): The element part string (e.g., "get_by_role('button')")

        Returns:
            tuple: A tuple containing the method name and a list of parameters.
        """
        try:
            # Extract the method name and parameters
            method_name = element_part.split('(')[0]
            params_str = element_part.split('(')[1].rstrip(')')
            params = eval(f'[{params_str}]')  # Safely evaluate parameters

            return method_name, params
        except Exception as e:
            raise ValueError(f"Failed to parse element part: {element_part}. Error: {str(e)}")

    def take_screenshot(self, full_page=False, mark_action=None):

        from PIL import Image

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        parsed_url = urllib.parse.urlparse(self.page.url)

        url_path = parsed_url.path
        if url_path == "/":
            url_path = "index.html"
        else:
            url_path = url_path.replace("/","_")
        
        if get_clean_website_name(url_path) != self.website_name:
            url_path = f"{get_clean_website_name(url_path)}_{url_path}"
            
        screenshot_path = os.path.join(self.screenshot_dir, f"{timestamp}_{url_path}.png")
        screenshot_bytes = self.page.screenshot(full_page=full_page, scale='css')
        
        if mark_action:
            image = self.mark_screenshot(screenshot_bytes, mark_action)
        else:
            image = Image.open(BytesIO(screenshot_bytes))
        
        image.save(screenshot_path, format='png')

        log.info(f"Screenshot {self.page.url} taken and saved to {screenshot_path}")
        #self.action_log.append(f"Screenshot {self.page.url} taken and saved to {screenshot_path}")
        self.session_screenshots.append(screenshot_path)

        return screenshot_bytes

    def mark_screenshot(self, screenshot_bytes, mark_action):
        """
        Marks the screenshot with the specified action.

        Parameters:
            screenshot_bytes (bytes): The bytes of the screenshot.
            mark_action (dict): Action details for marking the screenshot.
        """
        from PIL import Image, ImageDraw
        time.sleep(1) # maybe pass in bytes to avoid waiting for file to be written
        image = Image.open(BytesIO(screenshot_bytes))
        draw = ImageDraw.Draw(image)
        
        if mark_action['type'] == 'click':
            x, y = mark_action['position']
            radius = 10
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline='red', width=3)
        elif mark_action['type'] == 'type':
            x, y = mark_action['position']
            draw.rectangle((x-5, y-5, x+5, y+5), outline='blue', width=3)
        
        return image

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
            "last_actions": self.action_log,
            "session_goal": self.session_goal,
            "last_message": last_message
        }
        return prompt
    
    def check_llm_response(self, response):
        if isinstance(response, dict):
            output = response
        elif isinstance(response, str):
            output = json.loads(response)
        elif isinstance(response, list):
            log.warning(f'Response was a list, assuming its only new_instructions: {response=}')
            output = {
                'new_instructions' : response,
                'status': 'in-progress',
                'message': 'No message was received, which is a mistake by the assistant'
            }
        else:
            log.warning(f'Unknown response: {response=} {type(response)}')
            output = None
        
        if not output:
            log.error(f'Got no output from response: {response=}')
            return None

        if 'status' not in output:
            log.error(f'Response did not contain status')
            

        if 'new_instructions' not in output:
            log.warning(f'Response did not include new_instructions')
        
        if 'message' not in output:
            log.warning(f'Response did not include message')

        return output        

    def send_screenshot_to_llm(self, screenshot_bytes, last_message):

        encoded_image = base64.b64encode(screenshot_bytes).decode('utf-8')
        
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
        log.info(f"Session {self.session_id} finished")
        self.take_screenshot()
        self.save_cookies()
        self.browser.close()
        self.playwright.stop()
        self.save_action_log()
        self.create_gif_from_pngs()

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
            mark_action = None
            if not isinstance(instruction, dict):
                log.error(f"{instruction} {type(instruction)}")
            action = instruction['action']
            if action == 'navigate':
                self.navigate(instruction['url'])
            elif action == 'click':
                x,y = self.click(instruction['selector'])
                if (x,y) != (0,0):
                    mark_action = {'type':'click', 'position': (x,y)}
            elif action == 'scroll':
                self.scroll(instruction.get('direction', 'down'), 
                            int(instruction.get('amount', 1))
                            )
            elif action == 'type':
                x,y = self.type_text(instruction['selector'], instruction['text'])
                if (x,y) != (0,0):
                    mark_action = {'type':'type', 'position': (x,y)}
            elif action == 'execute':
                x,y,mark = self.execute_custom_command(instruction['command'])
                if mark:
                    mark_action = {'type': mark, 'position': (x,y)}
            self.steps += 1
            if self.steps >= self.max_steps:
                log.warning(f"Reached the maximum number of steps: {self.max_steps}")
                return
        time.sleep(2) 
        screenshot_bytes = self.take_screenshot(mark_action=mark_action)
        next_browser_instructions = self.send_screenshot_to_llm(
                screenshot_bytes, 
                last_message=last_message)
            
        return next_browser_instructions

    def create_gif_from_pngs(self, frame_duration=300):
        """
        Creates a GIF from a folder of PNG images.

        Args:
            folder_path (str): The path to the folder containing PNG images.
            output_gif_path (str): The path where the output GIF will be saved.
            duration (int): Duration between frames in milliseconds.

        Example:
            create_gif_from_pngs('/path/to/png_folder', '/path/to/output.gif', duration=500)
        """
        from PIL import Image

        folder_path=self.screenshot_dir
        output_gif_path = os.path.join(self.screenshot_dir, "session.gif")

        # List all PNG files in the folder
        png_files = [f for f in sorted(os.listdir(folder_path)) if f.endswith('.png')]

        # Open images and store them in a list
        images = [Image.open(os.path.join(folder_path, file)) for file in png_files]

        duration = len(images) * frame_duration
        # Save images as a GIF
        if images:
            images[0].save(
                output_gif_path,
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=0
            )
            print(f"GIF saved at {output_gif_path}")
        else:
            print("No PNG images found in the folder.")
    
    def start_session(self, instructions, session_goal):
            self.session_goal = session_goal

            if not instructions:
                instructions = [{'action': 'navigate', 'url': self.website_name}]

            next_instructions = self.execute_instructions(instructions)

            # load previous actions from same session
            self.load_action_log()

            in_session = True
            while in_session:
                if next_instructions and 'status' in next_instructions:
                    if next_instructions['status'] == 'in-progress':
                        log.info(f'Browser message: {next_instructions.get("message")}')
                        if 'new_instructions' not in next_instructions:
                            log.error('Browser status: "in-progress" but no new_instructions')
                        last_message = next_instructions['message']
                        self.action_log.append(last_message)
                        try:
                            next_instructions = self.execute_instructions(
                                next_instructions['new_instructions'], 
                                last_message=last_message)
                        except Exception as err:
                            log.error(f'session aborted due to: {str(err)}')
                            next_instructions = {
                                'status': 'error',
                                'message': f'session errored with: {str(err)}'
                            }
                            break
                    else:
                        log.info(f'Session finished due to status={next_instructions["status"]}')
                        in_session=False
                        break
                else:
                    log.info('Session finished due to next_instructions being empty')
                    in_session=False
                    break
            
            self.close()

            answer = None
            if next_instructions and next_instructions.get('status') == 'completed':
                answer = next_instructions.get('message'),
            
            return {
                "answer": answer,
                "metadata": {
                    "website": self.website_name,
                    "log": self.action_log,
                    "next_instructions": next_instructions,
                    "session_screenshots": self.session_screenshots,
                    "session_goal": self.session_goal,
                    "session_id": self.session_id,
                }
            }

