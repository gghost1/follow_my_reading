import { useState, useEffect, createContext } from "react";
import { useNavigate } from "react-router-dom";
import { fetchPdfsList } from "../api";
import Pagination from "../components/Pagination";

export const paginationContext = createContext();

function Home() {
    
    const [pageNum, setPageNum] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [documents, setDocuments] = useState(null);
    // const [loading, setLoading] = useState(true);
    // const [error, setError] = useState(null);

    // const handleSetPageNum = () => {
    //     setPageNum(pageNum + 1);
    // }

    const navigate = useNavigate();

    const handleOpenText = (id) => {
        navigate(`/${id}`);
    }

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchPdfsList(pageNum);
                console.log(data);
                const { total, items } = data;
                setTotalPages(Math.ceil(total/5));
                setDocuments(items);
                // setLoading(false);
            } catch (err) {
                console.error(err);
                // setError(err);
            }
        };
        fetchData();
    }, [pageNum]);

    useEffect(() => {
        
    }, [pageNum]);
    
    return ( 
    <>
        <h1>все пдфы</h1>

        <br /><br />

        {documents && documents.map((item) => (
            <div key={item.pdf_id}>
                <h2 onClick={() => handleOpenText(item.pdf_id)}>текст от пользователя {item.user_id}</h2>
                <p style={{fontSize: '10px'}}>{item.text}</p>
            </div>
        ))}
        
        <paginationContext.Provider value={{ pageNum, setPageNum, totalPages }}>
            <Pagination />
        </paginationContext.Provider>
    </>
    );
}

export default Home;