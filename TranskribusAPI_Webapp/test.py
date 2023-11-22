import streamlit as st
import xlsxwriter
from PIL import Image
import io

# Streamlit UI for uploading an image
st.title("Streamlit Excel Image Insertion")
uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_image is not None:
    # Read the uploaded image into a PIL Image object
    image = Image.open(uploaded_image)

    # Create a new Excel workbook
    workbook = xlsxwriter.Workbook('output.xlsx')
    worksheet = workbook.add_worksheet()

    # Convert the PIL Image to a bytes-like object
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')

    # Insert the in-memory image into the Excel worksheet with a filename
    worksheet.insert_image(0, 0, 'image.png', {'image_data': img_bytes})

    # Close the workbook to save it
    workbook.close()

    st.success("Image inserted into Excel sheet successfully!")

    # Add a download button for the Excel file
    st.download_button(
        label="Download Excel File",
        data='output.xlsx',
        key='download_button',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# To run the Streamlit app, use: streamlit run your_app.py