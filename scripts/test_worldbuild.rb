# frozen_string_literal: true

require "minitest/autorun"
require "tempfile"
require_relative "worldbuild"

class WorldbuildingEngineTest < Minitest::Test
  def fresh_state
    WorldbuildingEngine.template(
      title: "潮誓港",
      seed: "每次公开违誓都会让港湾退潮一寸",
      language: "zh-CN"
    )
  end

  def complete_rule
    {
      "id" => "RULE-oath-tide",
      "name" => "违誓退潮",
      "status" => "proposed",
      "capability" => "被公共见证系统承认的誓约可改变局部潮位基线",
      "impossibility" => "私下承诺、误解或无见证陈述不能直接改变潮位",
      "inputs" => ["公共见证", "已登记誓约"],
      "outputs" => ["局部潮位偏移"],
      "costs" => ["见证设施容量", "岸线工程调整"],
      "losses" => ["热与记录维护"],
      "access" => ["登记机关与当事人"],
      "visibility" => ["验潮尺可测"],
      "scale_limits" => ["只作用于登记港湾"],
      "failure_modes" => ["见证链断裂", "誓约文本冲突"],
      "maintenance" => ["校准验潮尺", "复核见证档案"],
      "countermeasures" => ["撤销登记", "隔离冲突记录"],
      "knowledge_layer" => "mixed",
      "dependencies" => [],
      "evidence" => ["proposal/oath-tide.md"]
    }
  end

  def test_template_is_structurally_valid
    result = WorldbuildingEngine::Validator.new(fresh_state).run
    assert result["valid"], result["errors"].join("\n")
    assert_equal 22, result.dig("stats", "facets")
    assert_equal 12, result.dig("stats", "pressure_tests")
  end

  def test_proposed_rule_requires_ledger
    state = fresh_state
    rule = complete_rule
    rule["maintenance"] = []
    state["rules"] << rule
    result = WorldbuildingEngine::Validator.new(state).run
    refute result["valid"]
    assert result["errors"].any? { |error| error.include?("maintenance") }
  end

  def test_canon_requires_evidence
    state = fresh_state
    state["premise"]["status"] = "canon"
    state["premise"]["core_difference"] = "潮位受公开誓约影响"
    state["premise"]["human_experience"] = "信誉会进入日常地理"
    state["premise"]["scale"] = "港城"
    state["premise"]["evidence"] = []
    result = WorldbuildingEngine::Validator.new(state).run
    refute result["valid"]
    assert_includes result["errors"], "canon premise 必须有 evidence"
  end

  def test_audit_keeps_framework_and_instance_maturity_separate
    state = fresh_state
    state["premise"].merge!(
      "core_difference" => "潮位受公开誓约影响",
      "human_experience" => "信誉会进入日常地理",
      "scale" => "港城"
    )
    state["rules"] << complete_rule
    first = state["facets"].first
    first["status"] = "partial"
    first["maturity"] = { "framework" => 4, "instance" => 1 }
    first["evidence"] = ["proposal/oath-tide.md"]
    result = WorldbuildingEngine::Auditor.new(state).run
    assert_equal 4, result.dig("facets", "framework_maturity", "maximum")
    assert_equal 1, result.dig("facets", "instance_maturity", "maximum")
    assert result.dig("gates", "foundation")
    refute result.dig("gates", "social_realism")
  end

  def test_audit_detects_framework_ahead_and_iteration_checkpoint
    state = fresh_state
    state["facets"].each do |facet|
      facet["status"] = "partial"
      facet["maturity"] = { "framework" => 5, "instance" => 1 }
      facet["evidence"] = ["proposal/overview.md"]
    end
    state["extensions"]["iteration"] = {
      "goal" => "持续完善港城",
      "persistence_scope" => "candidate-files",
      "round" => 6,
      "checkpoint_every" => 3,
      "last_checkpoint_round" => 3,
      "active_slice" => "港区—诊所—家庭纵切"
    }

    result = WorldbuildingEngine::Auditor.new(state).run
    assert_equal "framework-ahead", result.dig("iteration", "saturation")
    assert result.dig("iteration", "checkpoint_due")
    assert_equal ["cadence"], result.dig("iteration", "checkpoint_reasons")
    assert_equal "candidate-files", result.dig("iteration", "persistence_scope")
    assert result["high_leverage_actions"].any? { |action| action.include?("停止横向填表") }
    assert result["high_leverage_actions"].any? { |action| action.include?("全量检查点") }
  end


  def test_iteration_extension_ignores_invalid_round_values
    state = fresh_state
    state["extensions"]["iteration"] = {
      "round" => ["not", "a", "number"],
      "checkpoint_every" => { "bad" => true },
      "last_checkpoint_round" => -2
    }

    result = WorldbuildingEngine::Auditor.new(state).run
    assert_equal 0, result.dig("iteration", "round")
    assert_equal 3, result.dig("iteration", "checkpoint_every")
    refute result.dig("iteration", "checkpoint_due")
  end

  def test_route_uses_first_non_valid_owner_layer
    state = fresh_state
    assert_equal "fiction-core-zh:world-architect", WorldbuildingEngine::Router.new(state).run["skill"]
    state["fiction_core"]["world"]["status"] = "valid"
    state["fiction_core"]["character"]["status"] = "ready"
    assert_equal "fiction-core-zh:character-architect", WorldbuildingEngine::Router.new(state).run["skill"]
  end

  def test_world_change_invalidates_all_narrative_downstream_layers
    state = fresh_state
    %w[world character story outline prose].each do |layer|
      state["fiction_core"][layer]["status"] = "valid"
    end
    updated = WorldbuildingEngine::Invalidator.new(
      state,
      from: "world",
      reason: "核心潮汐规则改版",
      hard: true
    ).run
    %w[character story outline prose].each do |layer|
      assert_equal "invalidated", updated.dig("fiction_core", layer, "status")
      refute_empty updated.dig("fiction_core", layer, "invalidated_by")
    end
    result = WorldbuildingEngine::Validator.new(updated).run
    assert result["valid"], result["errors"].join("\n")
  end

  def test_duplicate_ids_are_rejected
    state = fresh_state
    state["rules"] << complete_rule
    state["actors"] << {
      "id" => "RULE-oath-tide",
      "name" => "同名冲突者",
      "status" => "draft",
      "summary" => "用于测试重复 ID",
      "evidence" => []
    }
    result = WorldbuildingEngine::Validator.new(state).run
    refute result["valid"]
    assert result["errors"].any? { |error| error.include?("ID 重复") }
  end
end
