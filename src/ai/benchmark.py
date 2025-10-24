"""
HOPPER - Model Benchmark
Benchmark automatique des modèles LLM/STT/TTS
"""

import time
import asyncio
from typing import Dict, List
from dataclasses import dataclass
from loguru import logger


@dataclass
class BenchmarkResult:
    """Résultat d'un benchmark"""
    model_name: str
    task_type: str  # "llm", "stt", "tts"
    latency_avg_ms: float
    latency_p95_ms: float
    throughput: float  # tokens/s pour LLM, audio_duration/process_time pour STT/TTS
    memory_peak_mb: float
    accuracy: float = 0.0  # Si applicable
    timestamp: str = ""


class ModelBenchmark:
    """
    Benchmark des modèles IA
    
    Features:
    - Benchmark LLM (latence, tokens/s, mémoire)
    - Benchmark STT (WER, latence)
    - Benchmark TTS (qualité, latence)
    - Comparaison A/B
    """
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        logger.info("📊 ModelBenchmark initialisé")
    
    async def benchmark_llm(
        self,
        model_name: str,
        prompts: List[str],
        ollama_host: str = "http://localhost:11434"
    ) -> BenchmarkResult:
        """Benchmark d'un modèle LLM"""
        import httpx
        from datetime import datetime
        
        latencies = []
        total_tokens = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for prompt in prompts:
                start = time.time()
                
                try:
                    response = await client.post(
                        f"{ollama_host}/api/generate",
                        json={
                            "model": model_name,
                            "prompt": prompt,
                            "stream": False
                        }
                    )
                    
                    latency = (time.time() - start) * 1000
                    latencies.append(latency)
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Estimer tokens (approximatif)
                        tokens = len(data.get("response", "").split()) * 1.3
                        total_tokens += tokens
                
                except Exception as e:
                    logger.error(f"Erreur benchmark LLM: {e}")
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
        throughput = total_tokens / (sum(latencies) / 1000) if latencies else 0
        
        result = BenchmarkResult(
            model_name=model_name,
            task_type="llm",
            latency_avg_ms=avg_latency,
            latency_p95_ms=p95_latency,
            throughput=throughput,
            memory_peak_mb=0,  # TODO: mesurer avec psutil
            timestamp=datetime.now().isoformat()
        )
        
        self.results.append(result)
        logger.info(f"✅ Benchmark {model_name}: {avg_latency:.0f}ms avg, "
                   f"{throughput:.1f} tokens/s")
        
        return result
    
    def compare_models(self, model_a: str, model_b: str) -> Dict:
        """Comparer 2 modèles"""
        results_a = [r for r in self.results if r.model_name == model_a]
        results_b = [r for r in self.results if r.model_name == model_b]
        
        if not results_a or not results_b:
            return {"error": "Données insuffisantes"}
        
        last_a = results_a[-1]
        last_b = results_b[-1]
        
        comparison = {
            "model_a": model_a,
            "model_b": model_b,
            "latency_diff_pct": ((last_b.latency_avg_ms - last_a.latency_avg_ms) / last_a.latency_avg_ms) * 100,
            "throughput_diff_pct": ((last_b.throughput - last_a.throughput) / last_a.throughput) * 100,
            "winner": model_a if last_a.latency_avg_ms < last_b.latency_avg_ms else model_b
        }
        
        return comparison


if __name__ == "__main__":
    # Test
    async def test():
        bench = ModelBenchmark()
        
        prompts = [
            "Bonjour, comment vas-tu?",
            "Explique-moi l'intelligence artificielle.",
            "Quelle est la capitale de la France?"
        ]
        
        result = await bench.benchmark_llm("mistral", prompts)
        print(f"Résultat: {result}")
    
    asyncio.run(test())
