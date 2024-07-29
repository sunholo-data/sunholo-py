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
import os
import pathlib
from ..custom_logging import log

def split_pdf_to_pages(pdf_path, temp_dir):

    log.info(f"Splitting PDF {pdf_path} into pages...")

    pdf_path = pathlib.Path(pdf_path)
    from pypdf import PdfReader, PdfWriter
    pdf = PdfReader(pdf_path)

    log.info(f"PDF file {pdf_path} contains {len(pdf.pages)} pages")

    # Get base name without extension
    basename = os.path.splitext(os.path.basename(pdf_path))[0]

    page_files = []
    
    if len(pdf.pages) == 1:
        #log.debug(f"Only one page in PDF {pdf_path} - sending back")
        return [str(pdf_path)]
    
    for page in range(len(pdf.pages)):
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf.pages[page])
        
        page_str = "{:02d}".format(page + 1)  
        output_filename = pathlib.Path(temp_dir, f'{basename}_p{page_str}.pdf')

        with open(output_filename, 'wb') as out:
            pdf_writer.write(out)

        log.info(f'Created PDF page: {output_filename}')
        page_files.append(str(output_filename))

    log.info(f"Split PDF {pdf_path} into {len(page_files)} pages...")
    return page_files

def read_pdf_file(pdf_path, metadata):
    from langchain.schema import Document
    from pypdf import PdfReader
    log.info(f"Trying local PDF parsing.  Reading PDF {pdf_path}...")

    pdf_path = pathlib.Path(pdf_path)
    
    pdf = PdfReader(pdf_path)

    try:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    except Exception as err:
        log.warning(f"Could not extract PDF via pypdf ERROR - {str(err)}")
        return None
    
    if len(text) < 10:
        log.info(f"Could not read PDF {pdf_path} via pypdf - too short, only got {text}")
        return None
    
    log.info(f"Successfully read PDF {pdf_path}...")
    return Document(page_content=text, metadata=metadata)