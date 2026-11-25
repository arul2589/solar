import { Route } from "react-router-dom";
import QuoteBuilder from "./pages/admin/QuoteBuilder";
import QuoteView from "./pages/public/QuoteView";

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
  </>
);
