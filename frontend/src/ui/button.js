import React from "react";

export function Button({ children, ...props }) {
  return (
    <button
      {...props}
      className="bg-blue-600 text-white font-semibold px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
    >
      {children}
    </button>
  );
}
