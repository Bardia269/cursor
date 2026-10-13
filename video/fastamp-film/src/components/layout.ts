import { useVideoConfig } from "remotion";

// Le film est recomposé (pas recadré) pour le 9:16 : chaque scène lit `v`.
export const useLayout = () => {
  const { width, height } = useVideoConfig();
  const v = height > width;
  return {
    v,
    W: width,
    H: height,
    pick: <T,>(horizontal: T, vertical: T): T => (v ? vertical : horizontal),
  };
};
