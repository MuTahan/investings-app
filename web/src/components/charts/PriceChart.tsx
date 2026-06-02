import {
  ColorType,
  createChart,
  type CandlestickData,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { Candle } from "../../models/market";
import { useThemeStore } from "../../store/themeStore";

function toSeriesData(candles: Candle[]): CandlestickData[] {
  return candles
    .map((c) => ({
      time: Math.floor(new Date(c.t).getTime() / 1000) as UTCTimestamp,
      open: c.o,
      high: c.h,
      low: c.l,
      close: c.c,
    }))
    .sort((a, b) => (a.time as number) - (b.time as number));
}

function readVar(name: string): string {
  if (typeof window === "undefined") return "#888";
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  // CSS vars are stored as "r g b" channels.
  return v ? `rgb(${v.replace(/\s+/g, ", ")})` : "#888";
}

export function PriceChart({ candles, height = 320 }: { candles: Candle[]; height?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  // Re-create the chart when the theme flips so colors stay correct.
  const theme = useThemeStore((s) => s.theme);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const muted = readVar("--muted");
    const grid = readVar("--border");
    const borderStrong = readVar("--border-strong");
    const bull = readVar("--bull");
    const bear = readVar("--bear");

    const chart = createChart(container, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: muted,
        fontSize: 11,
        fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: grid },
        horzLines: { color: grid },
      },
      rightPriceScale: { borderColor: borderStrong },
      timeScale: { borderColor: borderStrong, timeVisible: false },
      crosshair: { mode: 0 },
    });
    chartRef.current = chart;

    const series = chart.addCandlestickSeries({
      upColor: bull,
      downColor: bear,
      borderVisible: false,
      wickUpColor: bull,
      wickDownColor: bear,
    });
    series.setData(toSeriesData(candles));
    chart.timeScale().fitContent();

    const resize = () => chart.applyOptions({ width: container.clientWidth });
    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [candles, height, theme]);

  return <div ref={containerRef} className="w-full" />;
}
