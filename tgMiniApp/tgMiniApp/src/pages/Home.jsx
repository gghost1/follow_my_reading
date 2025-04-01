import { useState, useEffect, createContext } from 'react';
import { fetchPdfsList } from '../api';
import Pagination from '../components/Pagination';
import Loading from '../components/Loading';
import Text from '../components/TextComp';

export const paginationContext = createContext();

function Home() {
    const [pageNum, setPageNum] = useState(1);
    const [totalPages, setTotalPages] = useState(0);
    const [documents, setDocuments] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchPdfsList(pageNum);
                console.log(data);
                const { total, items } = data;
                setTotalPages(Math.ceil(total / 5));
                setDocuments(items);

            } catch (err) {
                console.error(err);
            }
        };
        fetchData();
    }, [pageNum]);

    useEffect(() => {}, [pageNum]);

    return (
        <>
            <h1>Все тексты</h1>
            <hr />
            <br />
            <br />
            <div className='textsD'>
            {documents ?
                documents.map((item) => (
                    <Text key={item.pdf_id} {...item} />
                ))
            :
                <Loading />
            }
            </div>

            <paginationContext.Provider value={{ pageNum, setPageNum, totalPages }}>
                <Pagination />
            </paginationContext.Provider>
        </>
    );
}

export default Home;
