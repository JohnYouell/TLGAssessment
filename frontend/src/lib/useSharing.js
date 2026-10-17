import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export const useSharing = () => {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.get("/sharing").then((r) => setData(r.data)).catch(() => {});
  }, []);
  return data;
};

export const shareBody = (s) => `${s.share_message}\n\nGet the book: ${window.location.origin}/book`;
