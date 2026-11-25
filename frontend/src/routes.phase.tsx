import { Route } from "react-router-dom";
import QuoteBuilder from "./pages/admin/QuoteBuilder";
import QuoteView from "./pages/public/QuoteView";
import { ProjectDetail, Projects } from "./pages/admin/Projects";

// Routes added in Phase 2 / 3
export const phase2Public = (
  <>
    <Route path="q/:token" element={<QuoteView />} />
    <Route path="status/:reference/quotation" element={<QuoteView />} />
  </>
);
export const phase2Admin = (
  <>
    <Route path="quotations/:id" element={<QuoteBuilder />} />
    <Route path="projects" element={<Projects />} />
    <Route path="projects/:id" element={<ProjectDetail />} />
  </>
);
