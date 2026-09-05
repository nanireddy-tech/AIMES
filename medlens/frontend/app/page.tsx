"use client";

import { useEffect, useState } from "react";

export default function Page() {
  const [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);
  return <main>{ready ? "MedLens dashboard is available at the local API root." : "Loading MedLens..."}</main>;
}
