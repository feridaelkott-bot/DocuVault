
#----------------------FIRST PROTOTYPE--------------------------

#Functions:
# 1. User uploads ONE document that can be of various types (listed in project description)
# 2. Create a "choose root directory" button
# 3. Once user has entered the document allow a parse button to be enabled
# 4. parse, through ONE document, (determining its type), and then build an output folder for the contents.


import json
import flet as ft
from pathlib import Path
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption
from docling.pipeline.simple_pipeline import SimplePipeline

from docling_core.types.doc import ImageRefMode, PictureItem, TextItem, SectionHeaderItem, ListItem, TableItem
from docling.datamodel.base_models import InputFormat

from docling.datamodel.pipeline_options import(
    PdfPipelineOptions,
    EasyOcrOptions
)
from datetime import datetime, timezone

def main(page: ft.Page):

    def parse_using_docling(file_path: Path):

        #inside the document converter you need to specify all the input options you're expecting, and with each of their pipelines
        converter = DocumentConverter(

            allowed_formats=[
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.XLSX,
                InputFormat.PPTX,
                InputFormat.HTML,
            ],

            format_options= {
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=PdfPipelineOptions(
                        ocr_options=EasyOcrOptions(
                            #for any pdf that is inputted, you'll force ocr on the whole page
                            force_full_page_ocr=True,
                        )
                    ),
                ),

                InputFormat.DOCX: WordFormatOption(
                    #simple pipeline is used for DOCX since DOCX already has formatted pages.
                    pipeline_cls=SimplePipeline
                )
            }
        )

        #timestamp:
        parse_started_at = datetime.now()

        conversion_result = converter.convert(file_path)

        parse_ended_at = datetime.now()

        total_time_taken_for_conversion = parse_ended_at - parse_started_at

        #content.md — full document rendered as Markdown
        # content.json — lossless structured JSON (DoclingDocument format)
        # tables/ — a subfolder containing each extracted table exported as a separate .csv file, named table_01.csv, table_02.csv, etc.
        # images/ — a subfolder containing each extracted image saved as a PNG file
        # metadata.json — document metadata (filename, format, parse timestamp, page count, table count, image count)

        #create content.md file:
        content_markdown = conversion_result.document.export_to_markdown()
        content_md_filename = "content.md"
        with open(content_md_filename, "w") as f:
            f.write(content_markdown)

        #create content.json file:
        #--> Docling Document is a unified parsed document representation, and export_to_dict() method will get you its lossless JSON output
        #--> so for this content.json file, all you need is the conv_res.document.export_to_dict()
        #so create the filename, and get the content to write into that file.
        content_json = conversion_result.document.export_to_dict()
        content_json_filename = "content.json"
        with open(content_json_filename, "w") as f:
            json.dump(content_json, f)



        #create a tables/ folder with the tables of the document each as a csv file
        tables_dir = Path("tables")
        tables_dir.mkdir(parents=True, exist_ok=True)
        for element, _level in conversion_result.document.iterate_items():
            count = 1

            if isinstance(element, TableItem):
                if count >= 10:
                    table_item_filename = f"image_{count}.csv"
                else:
                    table_item_filename = f"image_0{count}.csv"

                #get the table element and convert it to csv:
                with open(table_item_filename, "w") as f:
                    element.get_table(conversion_result.document).save(f, "CSV")

                count += 1

        #create a images/ folder, and for each image in the document, create a PNG file that is stored here.
        #--> first, create this directory:
        images_dir = Path("images")
        images_dir.mkdir(parents=True, exist_ok=True) #'parents' creates missing parent directories, 'exist_ok' prevents an error if the folder already exists
        for element, _level in conversion_result.document.iterate_items():
            count = 1

            if isinstance(element, PictureItem):
                if count >= 10:
                    image_item_filename = f"image_{count}.png"
                else:
                    image_item_filename = f"image_0{count}.png"

                #get the image element and convert it to PNG
                #open it with write as binary to write to the file's binary image.
                with open(image_item_filename, "w") as f:
                    element.get_image(conversion_result.document).save(f, "PNG")

                count += 1

        #todo: build a metadata.json file: get from the docling document:


        metadata_json_dict = {

            "filename": conversion_result.document.origin.filename,
            #MIME: multipurpose internet mail extensions -- a two-part label that tells a computer or web browser what kind of file or data it is receiving
            "format": conversion_result.document.origin.mimetype,
            "time_taken_for_conversion": total_time_taken_for_conversion,
            "time_stamp_starts":parse_started_at,
            "time_stamp_ends":parse_ended_at,
            "page_count": len(conversion_result.document.pages),
            "table_count": len(conversion_result.document.tables),
            "image_count": len(conversion_result.document.pictures)
        }

        with open("metadata.json", "w") as f:
            json.dump(metadata_json_dict, f)


        #TODO: form the rest of the files/folders
        #TODO: how would I create the large folder that contains everything the user needs
        #TODO: How would the user enter their desired file path through flet?
        #TODO: look at the specific pipeline options I have set up for PDF here, vs. standard PDF pipeline

    #create the file picker object, and on_result will call the function above when the user has chosen something
    file_picker = ft.FilePicker()

    page.services.append(file_picker) #-- there's a reason why we use this instead of page.add()

    #async is needed so that the rest of the UI does not freeze when you're uploading a document.
    #this function handles the user's choices, controlling what they can upload (must be async)
    async def upload_document_clicked(e):
        files = await file_picker.pick_files(
            #for now, in this prototype, only allow one file to be inputted
            allow_multiple=False,
            allowed_extensions=['pdf','docx', 'xlsx', 'pptx', 'html', 'png', 'jpg', 'jpeg', 'tiff']

        )

        if files:
            print("Got a file")
            selected_file = files[0].path
            parse_using_docling(selected_file)
        else:
            print("No file selected")

    page.add(
        ft.Button("Upload a Document :)",
                  on_click=upload_document_clicked,)
    )


 #create a "select file output destination"

ft.run(main)




#--------------------------NOTES--------------------------------

#You can use the export_to_markdown() function, and create a markdown file somewhere in your filesystem, using a Path object or a string.
#you can either use the mkdir method, or you can use the with file open... method

#pick_files() opens the file picker dialog
#on_result is a callback that Flet should call when that dialog closes
#e.files contains the selected files, or None if the user cancels their selection.

#await file_picker.pick_files() may also return the selected file list.
#therefore, you should only choose one place to process the files:
#--> Either in on_result, or after await pick_files() using what it returns

#using both is NOT an inherently infinite loop, but
#it can make the control flow confusing, and accidentally process the same file twice.

#my on_result handler was not even reached. This is NOT an infinite loop
#(infinite loops are caused by something being repeatedly called)

#The reason that the on_result was not working along with my own file picker code was probably
# due to configuration issues, and Flet version/API mismatches. Not necessarily a problem with the logic itself.
#this would be an interesting issue to look into, though it does not pertain to the actual completion of this capstone.






#TODO: I remember that the VLM pipeline option was better than the StandardPdfPipeline options at recognizing table structure
#I DO NOT KNOW WHY THIS IS. Also, what was "TableFormer"?
#however, I know that the VLM is trained on several types of tables, so recognizing the merged cells was "easier" for it to do than the standard OCR
#I recall that it wasn't perfect, but it was better. todo WHY?

