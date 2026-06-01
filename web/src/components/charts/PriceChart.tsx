import {
  ColorType,
  createChart,
  type CandlestickData,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import type { Candle } from "../../models/market";

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

export function PriceChart({ candles, height = 320 }: { candles: Candle[]; height?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8b98b0",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#1b2740" },
        horzLines: { color: "#1b2740" },
      },
      rightPriceScale: { borderColor: "#26324d" },
      timeScale: { borderColor: "#26324d", timeVisible: false },
      crosshair: { mode: 0 },
    });
    chartRef.current = chart;

    const series = chart.addCandlestickSeries({
      upColor: "#16a34a",
      downColor: "#dc2626",
      borderVisible: false,
      wickUpColor: "#16a34a",
      wickDownColor: "#dc2626",
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
  }, [candles, height]);

  return <div ref={containerRef} className="w-full" />;
}
