import { Dumbbell } from "lucide-react";

export const Loader = () => (
  <div data-testid="page-loader" className="flex min-h-[50vh] items-center justify-center">
    <Dumbbell className="h-8 w-8 animate-pulse text-gold" />
  </div>
);
