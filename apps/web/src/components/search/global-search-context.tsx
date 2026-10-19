"use client";

import { createContext, type ReactNode, useContext, useState } from "react";

type GlobalSearchState = {
  mailQuery: string;
  aiQuery: string;
  requestId: number;
};

type GlobalSearchContextValue = GlobalSearchState & {
  setMailQuery: (query: string) => void;
  searchAi: (query: string) => void;
};

const GlobalSearchContext = createContext<GlobalSearchContextValue | null>(null);

export function GlobalSearchProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<GlobalSearchState>({
    mailQuery: "",
    aiQuery: "",
    requestId: 0,
  });

  return (
    <GlobalSearchContext.Provider
      value={{
        ...state,
        setMailQuery: (mailQuery) =>
          setState((current) => ({ ...current, mailQuery })),
        searchAi: (query) =>
          setState((current) => ({
            ...current,
            aiQuery: query.trim(),
            requestId: current.requestId + 1,
          })),
      }}
    >
      {children}
    </GlobalSearchContext.Provider>
  );
}

export function useGlobalSearch() {
  const value = useContext(GlobalSearchContext);
  if (!value) {
    throw new Error("useGlobalSearch must be used inside GlobalSearchProvider");
  }
  return value;
}
