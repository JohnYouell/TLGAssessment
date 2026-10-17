import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export const useSharing = () => {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.get("/sharing").then((r) => setData(r.data)).catch(() => {});
  }, []);
  return data;
};

export const shareBody = (s) => (s.book_url ? `${s.share_message}\n\nGet the book: ${s.book_url}` : s.share_message);
