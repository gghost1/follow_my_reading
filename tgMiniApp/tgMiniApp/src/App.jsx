import { Routes, Route } from 'react-router-dom';

import Home from './pages/Home';
import TextDetail from './pages/TextDetail';

import './App.css';

function App() {


    return (
      <Routes>
        <Route path="/" element={<Home />}/>
        <Route path="/:id" element={<TextDetail />} />
      </Routes> 
    );
}

export default App;