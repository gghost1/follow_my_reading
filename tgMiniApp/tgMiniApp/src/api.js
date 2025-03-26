import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const fetchPdfData = async (pdfId) => {
    const res = await axios.get(`${API_BASE}/pdf_data/${pdfId}`);
    return res.data;
};

export const fetchPdfsList = async (pageNum, page_size = 5) => {
    const res = await axios.get(`${API_BASE}/pdfs`, {
        params: {
            page: pageNum,
            page_size,
          }
        }
    );
    return res.data;
};
