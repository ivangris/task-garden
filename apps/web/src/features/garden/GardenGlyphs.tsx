import type { JSX } from "react";

import type { DecorationVisualKey, PlantVisualKey } from "./asset-manifest";

type GlyphPosition = {
  x: number;
  y: number;
};

export function GardenPlantGlyph({
  visualKey,
  x,
  y,
}: GlyphPosition & { visualKey: PlantVisualKey }): JSX.Element {
  if (visualKey === "rare_bloom") {
    return (
      <g className="garden-glyph garden-glyph--bloom" transform={`translate(${x} ${y - 18})`}>
        <path d="M0 10 C-2 -6 0 -20 2 -34" className="garden-glyph__stem" />
        <path d="M0 -10 C-18 -8 -23 -20 -11 -25 C-2 -28 2 -20 2 -15" className="garden-glyph__leaf" />
        <path d="M1 -18 C15 -23 24 -16 18 -7 C12 0 4 -5 1 -9" className="garden-glyph__leaf garden-glyph__leaf--light" />
        <g transform="translate(2 -36)">
          {[0, 60, 120, 180, 240, 300].map((angle) => (
            <ellipse
              key={angle}
              cx="0"
              cy="-10"
              rx="6"
              ry="12"
              transform={`rotate(${angle})`}
              className="garden-glyph__petal"
            />
          ))}
          <circle r="5" className="garden-glyph__flower-center" />
        </g>
      </g>
    );
  }

  if (visualKey === "sage_clump") {
    return (
      <g className="garden-glyph garden-glyph--sage" transform={`translate(${x} ${y - 10})`}>
        {[-28, -16, -4, 8, 20, 31].map((offset, index) => (
          <ellipse
            key={offset}
            cx={offset * 0.48}
            cy={-18 - (index % 3) * 4}
            rx="11"
            ry="27"
            transform={`rotate(${offset * 0.8} ${offset * 0.48} -18)`}
            className={index % 2 === 0 ? "garden-glyph__sage-leaf" : "garden-glyph__sage-leaf garden-glyph__sage-leaf--light"}
          />
        ))}
      </g>
    );
  }

  return (
    <g className="garden-glyph garden-glyph--sprout" transform={`translate(${x} ${y - 10})`}>
      <path d="M0 8 C0 -2 1 -15 0 -28" className="garden-glyph__stem" />
      <path d="M0 -15 C-22 -10 -26 -27 -13 -31 C-3 -34 1 -24 1 -18" className="garden-glyph__leaf" />
      <path d="M1 -22 C17 -32 27 -22 21 -12 C15 -4 6 -10 1 -15" className="garden-glyph__leaf garden-glyph__leaf--light" />
    </g>
  );
}

export function GardenDecorationGlyph({
  visualKey,
  x,
  y,
}: GlyphPosition & { visualKey: DecorationVisualKey }): JSX.Element | null {
  if (visualKey === "fountain_core") {
    return null;
  }

  if (visualKey === "sun_arch") {
    return (
      <g className="garden-glyph garden-glyph--arch" transform={`translate(${x} ${y - 2})`}>
        <path d="M-34 12 V-17 C-34 -51 34 -51 34 -17 V12" className="garden-glyph__arch" />
        <circle cx="-34" cy="12" r="8" className="garden-glyph__stone" />
        <circle cx="34" cy="12" r="8" className="garden-glyph__stone" />
      </g>
    );
  }

  return (
    <g className="garden-glyph garden-glyph--path" transform={`translate(${x} ${y + 7})`}>
      <ellipse cx="-29" cy="0" rx="16" ry="8" className="garden-glyph__path-stone" />
      <ellipse cx="0" cy="5" rx="17" ry="8" className="garden-glyph__path-stone garden-glyph__path-stone--light" />
      <ellipse cx="30" cy="0" rx="16" ry="8" className="garden-glyph__path-stone" />
    </g>
  );
}

export function GardenCenterpiece({
  x,
  y,
  restored,
}: GlyphPosition & { restored: boolean }): JSX.Element {
  return (
    <g
      className={`garden-centerpiece ${restored ? "garden-centerpiece--restored" : "garden-centerpiece--waiting"}`}
      transform={`translate(${x} ${y + 9})`}
      aria-hidden="true"
    >
      <ellipse cx="0" cy="12" rx="52" ry="25" className="garden-centerpiece__shadow" />
      <ellipse cx="0" cy="4" rx="48" ry="24" className="garden-centerpiece__rim" />
      <ellipse cx="0" cy="0" rx="38" ry="18" className="garden-centerpiece__basin" />
      {restored ? (
        <>
          <ellipse cx="0" cy="-1" rx="31" ry="13" className="garden-centerpiece__water" />
          <path d="M0 -9 C-13 -34 -9 -51 0 -61 C9 -51 13 -34 0 -9Z" className="garden-centerpiece__stream" />
          <circle cx="0" cy="-35" r="5" className="garden-centerpiece__spark" />
          <ellipse cx="0" cy="-1" rx="23" ry="8" className="garden-centerpiece__ripple" />
        </>
      ) : (
        <>
          <path d="M-19 -4 L-6 2 L4 -8 L20 2" className="garden-centerpiece__crack" />
          <circle cx="0" cy="-12" r="10" className="garden-centerpiece__seed" />
        </>
      )}
    </g>
  );
}
