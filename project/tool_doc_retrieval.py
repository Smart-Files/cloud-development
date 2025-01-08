import math
from project.logger import logger
from langchain_community.document_loaders.html_bs import BSHTMLLoader
from langchain_community.document_loaders.text import TextLoader
from langchain_community.document_loaders.pdf import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, HTMLHeaderTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.vectorstores import VectorStoreRetriever
from langchain.tools.retriever import create_retriever_tool
from langchain.indexes import SQLRecordManager, index
from langchain_qdrant import Qdrant
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Query, Session
from langchain.indexes import _sql_record_manager
from pinecone import Pinecone, ServerlessSpec

UpsertionRecord = _sql_record_manager.UpsertionRecord


load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_ENDPOINT = os.getenv('QDRANT_ENDPOINT')

print("QDRANT_ENDPOINT", QDRANT_ENDPOINT)

embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model="text-embedding-3-large", chunk_size=400, dimensions=1024)

index_name = "smartfile-index"
# vectorstore = Qdrant(embeddings=embeddings, collection_name=index_name)
vectorstore = Qdrant.from_existing_collection(
    embedding=embeddings,
    collection_name=index_name,
    url=QDRANT_ENDPOINT,
    api_key=QDRANT_API_KEY,
)

namespace = f"pinecone/{index_name}"
record_manager = SQLRecordManager(
    namespace, db_url="sqlite:///record_manager_cache.sql"
)
record_manager.create_schema()



def _clear():
    """Hacky helper method to clear content. See the `full` mode section to to understand why it works."""
    index([], record_manager, vectorstore, cleanup="full", source_id_key="source")


def load_documents_db(directory: str, persist_dir: str = "db") -> Qdrant:
    documents = []
    dir_contents = os.listdir(directory)

    file_data = []
    with record_manager._make_session() as session:
        query: Query = session.query(UpsertionRecord)
        file_records: list[UpsertionRecord] = query.all()
        file_data = [record.group_id for record in file_records]
        session.commit()

    file_names = list(set(file_data))

    logger.info(f"Dir Contents (len: {len(dir_contents)}): {dir_contents}")
    logger.info(f"File Names (len: {len(file_names)}): {file_names}")

    if vectorstore and abs(len(file_names)-len(dir_contents)) <= 3:
        logger.info("Vectorstore already up to date -- skipping document loading.")
        return vectorstore
    else:
        logger.info("Vectorstore not up to date -- loading documents.")

    for filename in os.listdir(directory):
        if filename.startswith("."):
            continue
        file_path = os.path.join(directory, filename)
        loader = None
        extension = filename.split(".")[-1]
        match (extension):
            case "pdf":
                loader = PyPDFLoader(file_path)
                # index(loader, record_manager, vectorstore, cleanup="full", source_id_key="source")
                documents.extend(loader.load_and_split())
            case "html":
                loader = BSHTMLLoader(file_path, None, {"features": "html.parser"})
                # index(loader, record_manager, vectorstore, cleanup="full", source_id_key="source")
                documents.extend(loader.load())
            case _:
                loader = TextLoader(file_path)
                documents.extend(loader.load())
                # index(loader, record_manager, vectorstore, cleanup="full", source_id_key="source")

    # headers_to_split_on = [
    #     ("h1", "Header 1"),
    #     ("h2", "Header 2"),
    #     ("h3", "Header 3"),
    #     ("h4", "Header 4"),
    #     ("section", "Section"),
    # ]

    # html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    # html_header_splits = html_splitter.split_text(html_string)
    

    chunk_size = 500
    chunk_overlap = 30
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    docs = text_splitter.split_documents(documents)

    index(
        docs,
        record_manager,
        vectorstore,
        cleanup="full",
        source_id_key="source",
    )

    return vectorstore


def create_file_retrieval_tool(retriever):

    file_tool = create_retriever_tool(
        retriever,
        "search_file_tools_docs",
        """Searches and returns excerpts from documentation for CLI usage of the following tools:
        - pandoc
            - Pandoc is a library for converting from one markup format to another, and a command-line tool that uses this library. It can read markdown and (subsets of) reStructuredText, HTML, and LaTeX, and it can write markdown, reStructuredText, HTML, LaTeX, ConTeXt, PDF, RTF, DocBook XML, OpenDocument XML, ODT, Word docx, GNU Texinfo, MediaWiki markup, EPUB, FictionBook2, Textile, groff, etc.
        - ffmpeg
            - FFmpeg is a software suite of libraries and programs for handling video, audio, and other multimedia files and streams.  FFmpeg is designed for command-line-based processing of video and audio files and is used for format transcoding, basic editing (trimming and concatenation), video scaling, video post-production effects, and standards compliance (SMPTE, ITU).
        - image magick
            - ImageMagick is a CLI tool for displaying, converting, and editing raster image and vector image files. It can read and write over 200 image file formats. ImageMagick can resize, flip, mirror, rotate, distort, shear and transform images, adjust image colors, apply various special effects, or draw text, lines, polygons, ellipses, and Bézier curves.
        - poppler
            - Poppler is a library for rendering PDF documents. It includes the following tools:
            - pdfimages saves images from a PDF file as PPM, PBM, PNG, TIFF, JPEG, JPEG2000, or JBIG2 files.
            - pdftotext converts PDF files to plain text.
            - pdftocairo renders PDF files as Images using cairo.
            - pdftohtml converts PDF files to HTML.
            - pdfunite merges several PDF files into one PDF file.
        - dasel
            - Dasel is a command-line tool for querying, manipulating and converting JSON, YAML, and XML documents using a simple, intuitive, and expressive query language. 
        - csvkit
            - Includes tools such as:
            - in2csv: Converts various tabular data formats into CSV.
            - csvclean: Reports and fixes common errors in a CSV file.
            - csvcut: Filters and truncates CSV files. Like the Unix “cut” command, but for tabular data.
            - csvgrep: Filter tabular data to only those rows where certain columns contain a given value or match a regular expression.
            - csvjoin: Merges two or more CSV tables together using a method analogous to SQL JOIN operation. By default it performs an inner join, but full outer, left outer, and right outer are also available via flags.
            - csvsort: Sort CSV files. Like the Unix “sort” command, but for tabular data.
            - csvstack: Stack up the rows from multiple CSV files, optionally adding a grouping value to each row.
            - csvjson: Converts a CSV file into JSON or GeoJSON (depending on flags).
            - csvlook: Renders a CSV to the command line in a Markdown-compatible, fixed-width format.
            - csvstat: Prints descriptive statistics for all columns in a CSV file. Will intelligently determine the type of each column and then print analysis relevant to that type (ranges for dates, mean and median for integers, etc.)
            
        These tools will help you to execute operations with files.

        Search the documentation for the tool you want to use. For example: "pandoc convert markdown to pdf" will provide documentation on the pandoc tool for converting markdown files to PDF.
        """,
    )

    return file_tool