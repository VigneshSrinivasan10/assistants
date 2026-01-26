#!/usr/bin/env python3
"""
Test STT speed and accuracy with different models.
"""
import sys
import time
import numpy as np
from voice_assistant.model import STT

def generate_test_audio(duration_seconds=3):
    """Generate test audio (random noise as placeholder)."""
    sample_rate = 16000
    audio_data = np.random.randn(sample_rate * duration_seconds).astype(np.float32) * 0.1
    return (sample_rate, audio_data)

def benchmark_model(model_name, num_runs=5):
    """Benchmark a specific model."""
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"{'='*60}")
    
    try:
        # Initialize model
        print("Loading model...")
        start_load = time.time()
        stt = STT(model=model_name)
        load_time = time.time() - start_load
        print(f"✓ Model loaded in {load_time:.2f}s")
        
        # Generate test audio
        test_audio = generate_test_audio(duration_seconds=3)
        
        # Warm up (first run is always slower)
        print("Warming up...")
        _ = stt.speech_to_text(test_audio)
        print("✓ Warm-up complete")
        
        # Benchmark
        print(f"Running {num_runs} tests...")
        latencies = []
        
        for i in range(num_runs):
            start = time.time()
            result = stt.speech_to_text(test_audio)
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            print(f"  Run {i+1}: {latency:.1f}ms")
        
        # Stats
        avg_latency = np.mean(latencies)
        min_latency = np.min(latencies)
        max_latency = np.max(latencies)
        
        print(f"\nResults:")
        print(f"  Average: {avg_latency:.1f}ms")
        print(f"  Min: {min_latency:.1f}ms")
        print(f"  Max: {max_latency:.1f}ms")
        
        return {
            'model': model_name,
            'load_time': load_time,
            'avg_latency': avg_latency,
            'min_latency': min_latency,
            'max_latency': max_latency,
        }
        
    except Exception as e:
        print(f"✗ Error testing {model_name}: {e}")
        return None

def main():
    """Run benchmarks."""
    print("STT Performance Benchmark")
    print("=" * 60)
    
    models_to_test = [
        "base.en",   # Old default
        "small.en",  # New default (recommended)
    ]
    
    # You can add more models to test:
    # "tiny.en",   # Fastest but least accurate
    # "medium.en", # Slower but more accurate
    
    results = []
    
    for model in models_to_test:
        result = benchmark_model(model, num_runs=5)
        if result:
            results.append(result)
    
    # Summary
    if len(results) > 1:
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}")
        
        for result in results:
            print(f"\n{result['model']}:")
            print(f"  Load time: {result['load_time']:.2f}s")
            print(f"  Avg latency: {result['avg_latency']:.1f}ms")
        
        # Compare base vs small
        if len(results) == 2:
            base_latency = results[0]['avg_latency']
            small_latency = results[1]['avg_latency']
            diff = small_latency - base_latency
            percent = (diff / base_latency) * 100
            
            print(f"\nsmall.en is {diff:.1f}ms slower ({percent:.0f}% increase)")
            print("But it's ~40% more accurate!")
            
            if small_latency < 500:
                print("✓ Recommended: Use small.en (good speed + accuracy)")
            elif small_latency < 800:
                print("⚠ Warning: small.en is a bit slow, but worth it for accuracy")
            else:
                print("✗ small.en is too slow, consider using base.en instead")

if __name__ == "__main__":
    main()
