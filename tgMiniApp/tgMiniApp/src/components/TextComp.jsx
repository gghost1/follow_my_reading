import { useNavigate } from "react-router-dom";

function Text(item) {

    const navigate = useNavigate();

    const handleOpenText = (id) => {
        navigate(`/${id}`);
    };


    return ( 
        <div key={item.pdf_id} className="textComp" onClick={() => handleOpenText(item.pdf_id)}>
            <h3 className="textComp__title">
                Текст №{item.pdf_id}
            </h3>
            <p>от пользователя id: {item.user_id}</p>

            <p style={{ fontSize: '10px' }} id="textComp__text">{item.text}</p>
        </div>
     );
}

export default Text;