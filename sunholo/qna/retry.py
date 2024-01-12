#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import time
from httpcore import ReadTimeout
from httpx import ReadTimeout
import traceback
from ..logging import setup_logging

logging = setup_logging()

def retry_qna(qa_function, question, max_retries=1, initial_delay=5):
    for retry in range(max_retries):
        try:
            return qa_function(question)
        except ReadTimeout as err:
            delay = initial_delay * (retry + 1)
            logging.warning(f"Read timeout while asking: {question} - trying again after {delay} seconds. Error: {str(err)}")
            time.sleep(delay)
            try:
                result = qa_function(question)
                result["answer"] = result["answer"] + " (Sorry for the delay, brain was a bit slow - should be quicker next time)"
                return result
            except ReadTimeout:
                if retry == max_retries - 1:
                    raise
        except Exception as err:
            delay = initial_delay * (retry + 1)
            logging.error(f"General error: {traceback.format_exc()}")
            time.sleep(delay)
            try:
                result = qa_function(question)
                result["answer"] = result["answer"] + " (Sorry for the delay, had to warm up the brain - should be quicker next time)"
                return result
            except Exception:
                if retry == max_retries - 1:
                    raise

    raise Exception(f"Max retries exceeded for question: {question}")