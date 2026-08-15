🧠 System Invalidation & Error Management Architecture

To keep the forecaster from hallucinating or generating static predictions, 
it validates its performance using a programmatic Post-Mortem Evaluation Layer:

1. The Invalidation Threshold: As embedded in the forecast payload above, the model
automatically creates mathematical boundaries (e.g., a 5% price drop or a negative shift in news sentiment).
If the real-world metric breaks these boundaries during the 7-day tracking window,
the forecast is automatically flagged as INVALIDATED in the database rather than waiting for the deadline.

2. Backtesting & Verification Daemon: A daily script checks previous records against actual spot outcomes.
It evaluates the system using a Mean Absolute Percentage Error (MAPE) metric.

3. Self-Correction Logic (Dynamic Weighting): If the historical error rate spikes above 15%, the system decreases 
the weight of the underperforming data source (e.g., reducing sentiment weight from 40% to 20%) and increases
the weight of structural market momentum. 
This ensures the model adapts automatically to changing market conditions.

