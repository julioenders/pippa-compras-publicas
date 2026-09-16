import { Routes, Route } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import Home from './pages/Home'
import GestorPublico from './pages/GestorPublico'
import SebraeNacional from './pages/SebraeNacional'
import SebraeUF from './pages/SebraeUF'
import MPE from './pages/MPE'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="gestor-publico" element={<GestorPublico />} />
        <Route path="sebrae-nacional" element={<SebraeNacional />} />
        <Route path="sebrae-uf/:uf" element={<SebraeUF />} />
        <Route path="mpe" element={<MPE />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
