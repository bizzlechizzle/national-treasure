# Integration Patterns

How to deploy ML models in production systems.

---

## Pattern Overview

| Pattern | Latency | Complexity | Best For |
|---------|---------|------------|----------|
| **Batch prediction** | Hours | Low | Periodic scoring, reports |
| **Request-response API** | <100ms | Medium | Real-time, user-facing |
| **Streaming** | Seconds | High | Continuous data, event-driven |
| **Embedded model** | <10ms | Medium | Edge, mobile, IoT |
| **Feature store** | Varies | High | Shared features, real-time + batch |

---

## Batch Prediction

Run predictions on a schedule (hourly, daily, weekly).

### When to Use

- Predictions don't need to be real-time
- Large volumes to process
- Same predictions reused multiple times
- Cost optimization (GPU time)

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Data      │────▶│   Batch     │────▶│   Results   │
│   Store     │     │   Job       │     │   Table     │
└─────────────┘     └─────────────┘     └─────────────┘
                          ↓
                    ┌─────────────┐
                    │   Model     │
                    │   (loaded)  │
                    └─────────────┘
```

### Implementation

```python
# batch_predict.py - Run as scheduled job

import pandas as pd
import joblib
from datetime import datetime

def batch_predict():
    # Load model once
    model = joblib.load('model.pkl')
    preprocessor = joblib.load('preprocessor.pkl')

    # Load data
    df = pd.read_sql("""
        SELECT * FROM customers
        WHERE last_prediction_date < CURRENT_DATE - INTERVAL '1 day'
        OR last_prediction_date IS NULL
    """, connection)

    # Preprocess
    X = preprocessor.transform(df[feature_columns])

    # Predict in batches (memory efficiency)
    batch_size = 10000
    predictions = []
    for i in range(0, len(X), batch_size):
        batch = X[i:i+batch_size]
        preds = model.predict_proba(batch)[:, 1]
        predictions.extend(preds)

    # Save results
    df['churn_probability'] = predictions
    df['prediction_date'] = datetime.now()
    df[['customer_id', 'churn_probability', 'prediction_date']].to_sql(
        'churn_predictions', connection, if_exists='append'
    )

if __name__ == '__main__':
    batch_predict()
```

### Scheduling

| Tool | Use Case |
|------|----------|
| **Cron** | Simple, single machine |
| **Airflow** | Complex DAGs, dependencies |
| **Prefect** | Modern Python-native |
| **Dagster** | Data-aware orchestration |
| **Cloud Scheduler** | Managed (GCP, AWS) |

---

## Request-Response API

Real-time predictions via HTTP/gRPC API.

### When to Use

- User-facing applications
- Latency matters (<100ms typical)
- One or few predictions at a time
- Need immediate response

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   API       │────▶│   Model     │
│   (App)     │◀────│   Server    │◀────│   Service   │
└─────────────┘     └─────────────┘     └─────────────┘
```

### FastAPI Implementation

```python
# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI()

# Load model at startup (once)
model = None
preprocessor = None

@app.on_event("startup")
async def load_model():
    global model, preprocessor
    model = joblib.load('model.pkl')
    preprocessor = joblib.load('preprocessor.pkl')

class PredictionRequest(BaseModel):
    age: float
    income: float
    category: str
    region: str

class PredictionResponse(BaseModel):
    probability: float
    prediction: int
    model_version: str = "1.0.0"

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        # Convert to dataframe
        import pandas as pd
        df = pd.DataFrame([request.dict()])

        # Preprocess
        X = preprocessor.transform(df)

        # Predict
        prob = model.predict_proba(X)[0, 1]
        pred = int(prob > 0.5)

        return PredictionResponse(
            probability=float(prob),
            prediction=pred
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "model_loaded": model is not None}
```

### Latency Optimization

| Technique | Impact | How |
|-----------|--------|-----|
| **Model loading** | Startup | Load once at startup, not per request |
| **ONNX conversion** | 2-3x | Export to ONNX, use ONNX Runtime |
| **Quantization** | 2-4x | Reduce precision (FP16, INT8) |
| **Batching** | Throughput | Batch multiple requests |
| **Caching** | Variable | Cache frequent predictions |
| **Feature precomputation** | Latency | Precompute slow features |

```python
# ONNX conversion for faster inference
import skl2onnx
from skl2onnx.common.data_types import FloatTensorType

initial_type = [('float_input', FloatTensorType([None, n_features]))]
onnx_model = skl2onnx.convert_sklearn(model, initial_types=initial_type)

# Save
with open("model.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

# Load and run with ONNX Runtime
import onnxruntime as ort
session = ort.InferenceSession("model.onnx")
pred = session.run(None, {"float_input": X.astype(np.float32)})
```

---

## Streaming / Event-Driven

Process events in real-time as they arrive.

### When to Use

- Continuous data streams
- Need to react to events
- Latency: seconds acceptable
- High throughput

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Events    │────▶│   Stream    │────▶│   Output    │
│   (Kafka)   │     │   Processor │     │   (Kafka)   │
└─────────────┘     └─────────────┘     └─────────────┘
                          ↓
                    ┌─────────────┐
                    │   Model     │
                    └─────────────┘
```

### Kafka + Python Example

```python
# streaming_predictor.py
from kafka import KafkaConsumer, KafkaProducer
import json
import joblib

# Load model
model = joblib.load('model.pkl')
preprocessor = joblib.load('preprocessor.pkl')

# Kafka setup
consumer = KafkaConsumer(
    'input-events',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda m: json.dumps(m).encode('utf-8')
)

def process_event(event):
    """Process single event and return prediction."""
    import pandas as pd
    df = pd.DataFrame([event])
    X = preprocessor.transform(df)
    prob = model.predict_proba(X)[0, 1]
    return {
        'event_id': event.get('id'),
        'probability': float(prob),
        'timestamp': event.get('timestamp')
    }

# Main loop
for message in consumer:
    event = message.value
    result = process_event(event)
    producer.send('predictions', value=result)
```

### Streaming Frameworks

| Framework | Use Case | Language |
|-----------|----------|----------|
| **Kafka Streams** | JVM ecosystem | Java/Scala |
| **Flink** | Complex event processing | Java/Python |
| **Spark Streaming** | Large scale, batch + stream | Python/Scala |
| **Bytewax** | Python-native streaming | Python |
| **River** | Online ML specifically | Python |

---

## Embedded Model

Deploy model directly in application or on device.

### When to Use

- Edge devices (IoT, mobile)
- Ultra-low latency (<10ms)
- Offline capability
- Privacy (data stays on device)

### Formats

| Format | Use Case | Size |
|--------|----------|------|
| **ONNX** | Cross-platform | Medium |
| **TensorFlow Lite** | Mobile, embedded | Small |
| **Core ML** | iOS/macOS | Small |
| **PMML** | Enterprise systems | Large |
| **Pickle/Joblib** | Python only | Variable |

### TensorFlow Lite Example

```python
# Convert to TFLite
import tensorflow as tf

# Assume you have a Keras model
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]  # Quantize
tflite_model = converter.convert()

with open('model.tflite', 'wb') as f:
    f.write(tflite_model)

# Run inference (on device)
interpreter = tf.lite.Interpreter(model_path='model.tflite')
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

interpreter.set_tensor(input_details[0]['index'], input_data)
interpreter.invoke()
output = interpreter.get_tensor(output_details[0]['index'])
```

### Size Optimization

| Technique | Size Reduction | Accuracy Impact |
|-----------|----------------|-----------------|
| **Quantization (FP16)** | 2x | Minimal |
| **Quantization (INT8)** | 4x | Small |
| **Pruning** | 2-10x | Variable |
| **Knowledge distillation** | Variable | Depends on teacher |

---

## Feature Store

Centralized feature management for training and serving.

### When to Use

- Multiple models share features
- Need consistency between training and serving
- Real-time + batch features needed
- Team collaboration on features

### Architecture

```
┌─────────────┐                    ┌─────────────┐
│   Batch     │──── Features ─────▶│   Feature   │
│   Pipeline  │                    │   Store     │
└─────────────┘                    └─────────────┘
                                        │
┌─────────────┐                         │
│   Streaming │──── Features ───────────┤
│   Pipeline  │                         │
└─────────────┘                         │
                                        ↓
                   ┌─────────────┐ ◀── Online ────┐
                   │   Training  │                │
                   └─────────────┘                │
                                                  │
                   ┌─────────────┐ ◀── Online ────┘
                   │   Serving   │
                   └─────────────┘
```

### Feast Example

```python
# feature_repo.py
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64

# Define entity
customer = Entity(
    name="customer",
    join_keys=["customer_id"]
)

# Define feature view
customer_features = FeatureView(
    name="customer_features",
    entities=[customer],
    schema=[
        Field(name="total_purchases", dtype=Float32),
        Field(name="days_since_signup", dtype=Int64),
        Field(name="avg_order_value", dtype=Float32),
    ],
    source=FileSource(
        path="data/customer_features.parquet",
        timestamp_field="event_timestamp"
    )
)

# Apply to feature store
# feast apply

# Get features for training
from feast import FeatureStore
store = FeatureStore(repo_path=".")

training_df = store.get_historical_features(
    entity_df=entity_df,  # customer_id + timestamp
    features=["customer_features:total_purchases",
              "customer_features:avg_order_value"]
).to_df()

# Get features for serving (online)
feature_vector = store.get_online_features(
    features=["customer_features:total_purchases"],
    entity_rows=[{"customer_id": 123}]
).to_dict()
```

### Feature Store Options

| Tool | Type | Best For |
|------|------|----------|
| **Feast** | Open source | Getting started, flexible |
| **Tecton** | Managed | Enterprise, real-time |
| **SageMaker Feature Store** | AWS | AWS-native |
| **Vertex AI Feature Store** | GCP | GCP-native |
| **Databricks Feature Store** | Databricks | Lakehouse architecture |

---

## Model Serving Platforms

### Comparison

| Platform | Best For | Features |
|----------|----------|----------|
| **BentoML** | Python-first, flexible | Easy packaging, multi-model |
| **MLflow** | Experiment tracking + deploy | Full MLOps lifecycle |
| **TensorFlow Serving** | TF models at scale | High performance, gRPC |
| **TorchServe** | PyTorch models | Model archiving, handlers |
| **Triton** | GPU inference at scale | Multi-framework, batching |
| **Seldon** | Kubernetes-native | Advanced deployments |
| **KServe** | Kubernetes, serverless | Autoscaling, canary |

### BentoML Example

```python
# service.py
import bentoml
from bentoml.io import JSON, NumpyNdarray
import numpy as np

# Save model
bentoml.sklearn.save_model("churn_model", model)

# Create service
runner = bentoml.sklearn.get("churn_model:latest").to_runner()
svc = bentoml.Service("churn_service", runners=[runner])

@svc.api(input=NumpyNdarray(), output=JSON())
async def predict(input_array: np.ndarray) -> dict:
    result = await runner.predict_proba.async_run(input_array)
    return {"probabilities": result.tolist()}

# Build and serve
# bentoml build
# bentoml serve service:svc
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Model serialized and versioned
- [ ] Preprocessing pipeline included
- [ ] Input validation implemented
- [ ] Error handling complete
- [ ] Health check endpoint
- [ ] Logging configured
- [ ] Latency tested under load

### Production Monitoring

- [ ] Prediction logging
- [ ] Input distribution tracking
- [ ] Latency monitoring
- [ ] Error rate alerting
- [ ] Model drift detection
- [ ] A/B test infrastructure

### Rollout Strategy

| Strategy | Risk | Use When |
|----------|------|----------|
| **Big bang** | High | Low-stakes, well-tested |
| **Shadow mode** | Low | Run parallel, compare |
| **Canary** | Medium | Gradual rollout % |
| **A/B test** | Low | Need statistical comparison |
| **Feature flag** | Low | Easy rollback |

---

## Common Integration Mistakes

| Mistake | Consequence | Prevention |
|---------|-------------|------------|
| Different preprocessing | Wrong predictions | Use same pipeline |
| Model loaded per request | Slow, OOM | Load once at startup |
| No input validation | Crashes, bad predictions | Validate schema |
| No health checks | Silent failures | Add /health endpoint |
| No logging | Can't debug | Log inputs, outputs, errors |
| No versioning | Can't rollback | Version models explicitly |
| Synchronous heavy compute | Blocked requests | Use async/background |

---

## Quick Architecture Decision

```
What's your latency requirement?
│
├─► Hours acceptable → BATCH
│   └─► Scheduled job (Airflow, cron)
│
├─► Seconds acceptable → STREAMING
│   └─► Kafka + processor
│
├─► <100ms needed → REQUEST-RESPONSE API
│   ├─► Low volume → FastAPI
│   └─► High volume → Model server (Triton, TF Serving)
│
└─► <10ms, offline → EMBEDDED
    └─► TFLite, ONNX, Core ML
```

---

## Further Reading

| Resource | Type | URL |
|----------|------|-----|
| FastAPI ML Deployment | Tutorial | https://fastapi.tiangolo.com/deployment/ |
| BentoML Docs | Library | https://docs.bentoml.org/ |
| Feast Feature Store | Library | https://docs.feast.dev/ |
| MLflow Model Serving | Docs | https://mlflow.org/docs/latest/models.html |
| Triton Inference Server | Docs | https://developer.nvidia.com/triton-inference-server |
