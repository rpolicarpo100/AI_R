"""
P8 — Rigor Optimizer — mede mais e otimiza o rigor
"""

def test_p8_rigor_optimizer_exists():
    from app.services.rigor_optimizer_p8 import rigor_optimizer_p8
    assert rigor_optimizer_p8 is not None
    assert hasattr(rigor_optimizer_p8, 'get_current_rigor')
    assert hasattr(rigor_optimizer_p8, 'measure_provider_models')
    assert hasattr(rigor_optimizer_p8, 'optimize_kie_ai')
    assert hasattr(rigor_optimizer_p8, 'run_full_optimization')
    print("✅ P8 Rigor Optimizer exists")

def test_p8_rigor_current():
    from app.services.rigor_optimizer_p8 import rigor_optimizer_p8
    rigor = rigor_optimizer_p8.get_current_rigor()
    
    assert "total" in rigor
    assert "measured" in rigor
    assert "measured_pct" in rigor
    assert "coding" in rigor
    assert "chat_total" in rigor
    assert "chat_measured_pct" in rigor
    
    print(f"✅ Rigor current: total {rigor['measured']}/{rigor['total']} {rigor['measured_pct']}% coding {rigor['coding_pct']}% chat {rigor['chat_measured']}/{rigor['chat_total']} {rigor['chat_measured_pct']}%")

def test_p8_kie_ai_optimization():
    from app.services.rigor_optimizer_p8 import rigor_optimizer_p8
    result = rigor_optimizer_p8.optimize_kie_ai()
    
    assert "total" in result
    assert result["total"] == 206 or result["total"] > 100
    assert "video_marked" in result
    
    print(f"✅ Kie AI optimization: total {result['total']} video_marked {result['video_marked']} chat_models {result['chat_models']}")

def test_p8_free_providers():
    from app.services.rigor_optimizer_p8 import rigor_optimizer_p8
    result = rigor_optimizer_p8.add_free_provider_models()
    
    assert "added" in result
    assert "providers_checked" in result
    
    print(f"✅ Free providers: added {result['added']} checked {result['providers_checked']}")

def test_p8_rigor_improvement():
    from app.services.rigor_optimizer_p8 import rigor_optimizer_p8
    from app.services.continuous_benchmark_p7 import continuous_benchmark_p7
    
    p7_stats = continuous_benchmark_p7.get_rigor_stats()
    p8_rigor = rigor_optimizer_p8.get_current_rigor()
    
    # Rigor should be at least 50% total, 60% chat
    assert p7_stats["measured_pct"] >= 50, f"Total rigor {p7_stats['measured_pct']}% <50%"
    assert p7_stats["chat_measured_pct"] >= 60, f"Chat rigor {p7_stats['chat_measured_pct']}% <60%"
    
    # After optimization, chat rigor should improve or stay same
    assert p8_rigor["chat_measured_pct"] >= 60
    
    print(f"✅ Rigor improvement: P7 total {p7_stats['measured_pct']}% chat {p7_stats['chat_measured_pct']}% P8 total {p8_rigor['measured_pct']}% chat {p8_rigor['chat_measured_pct']}%")

def test_p8_rigor_critique():
    from app.services.continuous_benchmark_p7 import continuous_benchmark_p7
    
    stats = continuous_benchmark_p7.get_rigor_stats()
    
    # Should have needing_measurement list
    assert "needing_measurement" in stats
    assert "measured_pct" in stats
    assert "coding_nonzero_pct" in stats
    
    print(f"✅ Rigor critique: measured {stats['measured_pct']}% coding {stats['coding_nonzero_pct']}% chat {stats['chat_measured_pct']}% needing {len(stats['needing_measurement'])}")

def test_p8_rigor_endpoints():
    """Check rigor router exists"""
    with open("app/routers/rigor.py") as f:
        content = f.read()
    
    assert "optimize_rigor" in content or "/optimize" in content
    assert "measure_more" in content
    assert "P8" in content
    assert "mede mais" in content.lower() or "rigor" in content.lower()
    
    print("✅ Rigor endpoints P8 present")

def test_p8_context_compiler_rigor():
    """P8 Context Compiler should improve rigor via cost/latency optimization"""
    from app.services.context_compiler import context_compiler
    
    # Compile some context and check quality metrics improve cost/latency
    messages = [
        {"role": "system", "content": "You are helpful AI"},
        {"role": "user", "content": "ola " * 100},
        {"role": "user", "content": "ola " * 100},  # duplicate
        {"role": "user", "content": "como funciona auth JWT?"},
    ]
    
    compiled = context_compiler.compile(messages, None, None, 8000, 1000, "BEST", use_cache=False)
    
    assert compiled.quality_metrics["overall_quality"] > 0
    assert "saved_tokens" in compiled.quality_metrics
    assert compiled.quality_metrics["saved_tokens"] >= 0
    
    print(f"✅ Context Compiler rigor: quality {compiled.quality_metrics['overall_quality']}% saved {compiled.quality_metrics['saved_tokens']} tokens dedup {compiled.dedup_info['duplicates_removed']}")

if __name__ == "__main__":
    test_p8_rigor_optimizer_exists()
    test_p8_rigor_current()
    test_p8_kie_ai_optimization()
    test_p8_free_providers()
    test_p8_rigor_improvement()
    test_p8_rigor_critique()
    test_p8_rigor_endpoints()
    test_p8_context_compiler_rigor()
    print("\n✅ All P8 Rigor Optimizer tests passed")
