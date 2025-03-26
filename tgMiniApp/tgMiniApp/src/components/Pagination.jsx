import { useState, useEffect, useContext } from 'react';
import { paginationContext } from '../pages/Home';

export default function Pagination() {
    const { pageNum, setPageNum, totalPages } = useContext(paginationContext);
    const [activePage, setActivePage] = useState(1);

    const handleUpdatePage = (num) => {
        setPageNum(num);
    };

    useEffect(() => {
        setActivePage(1);
    }, [totalPages]);

    return (
        <div className="paginationContainer">
            {[...Array(totalPages)].map((_, i) => {
                const page = i + 1;
                return (
                    <button
                        key={page}
                        onClick={() => handleUpdatePage(page)}
                        className={`pagItem ${page === pageNum ? 'pagItemActive' : ''}`}
                    >
                        {page}
                    </button>
                );
            })}
        </div>
    );
}
