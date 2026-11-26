import { Navigate, Route, Routes } from "react-router-dom";
import { defaultSlug } from "./api";
import Account from "./pages/admin/Account";
import AdminLayout from "./pages/admin/AdminLayout";
import Catalogue from "./pages/admin/Catalogue";
import Login from "./pages/admin/Login";
import { Calculator, Emails, Platform, Users } from "./pages/admin/Misc";
import Pipeline from "./pages/admin/Pipeline";
import RequestDetail from "./pages/admin/RequestDetail";
import Settings from "./pages/admin/Settings";
import CustomerLogin from "./pages/public/CustomerLogin";
import About from "./pages/public/About";
import Landing from "./pages/public/Landing";
import CalculatorPage from "./pages/public/CalculatorPage";
import HowItWorks from "./pages/public/HowItWorks";
import Products from "./pages/public/Products";
import Projects from "./pages/public/Projects";
import SolutionPage from "./pages/public/SolutionPage";
import PublicLayout from "./pages/public/PublicLayout";
import RequestForm from "./pages/public/RequestForm";
import Status from "./pages/public/Status";
import { phase2Admin, phase2Public } from "./routes.phase";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={`/s/${defaultSlug()}`} replace />} />
      <Route path="/s/:slug" element={<PublicLayout />}>
        <Route index element={<Landing />} />
        <Route path="about" element={<About />} />
        <Route path="residential" element={<SolutionPage kind="residential" />} />
        <Route path="commercial" element={<SolutionPage kind="commercial" />} />
        <Route path="industrial" element={<SolutionPage kind="industrial" />} />
        <Route path="products" element={<Products />} />
        <Route path="calculator" element={<CalculatorPage />} />
        <Route path="how-it-works" element={<HowItWorks />} />
        <Route path="projects" element={<Projects />} />
        <Route path="request" element={<RequestForm />} />
        <Route path="status/:reference" element={<Status />} />
        <Route path="login" element={<CustomerLogin />} />
        {phase2Public}
      </Route>
      <Route path="/admin/login" element={<Login />} />
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Pipeline />} />
        <Route path="requests/:id" element={<RequestDetail />} />
        <Route path="calculator" element={<Calculator />} />
        <Route path="catalogue" element={<Catalogue />} />
        <Route path="settings" element={<Settings />} />
        <Route path="users" element={<Users />} />
        <Route path="emails" element={<Emails />} />
        <Route path="platform" element={<Platform />} />
        <Route path="account" element={<Account />} />
        {phase2Admin}
      </Route>
      <Route path="*" element={<p style={{ padding: 20 }}>Page not found.</p>} />
    </Routes>
  );
}
