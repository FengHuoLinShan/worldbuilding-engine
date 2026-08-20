#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "optparse"
require "time"
require "fileutils"
require "securerandom"

module WorldbuildingEngine
  VERSION = "0.5.0"
  SCHEMA_VERSION = "0.1.0"
  PLUGIN_ROOT = File.expand_path("..", __dir__)
  TEMPLATE_PATH = File.join(
    PLUGIN_ROOT,
    "skills",
    "worldbuilding-engine",
    "assets",
    "world-project-template",
    "world-state.json"
  )
  PROJECT_TEMPLATE_PATH = File.join(
    PLUGIN_ROOT,
    "skills",
    "worldbuilding-engine",
    "assets",
    "world-project-template",
    "PROJECT.md"
  )

  TOP_LEVEL_KEYS = %w[
    schema_version engine_version project authority premise knowledge_layers rules
    reproduction_loops facets coupling_chains situated_tests pressure_tests actors
    places institutions history fiction_core dependencies change_log audit extensions
  ].freeze

  AUTHORITY_STATUSES = %w[draft proposed canon author-required deprecated].freeze
  COVERAGE_STATUSES = %w[gap partial covered not-applicable].freeze
  PRESSURE_STATUSES = %w[not-run pass mixed fail].freeze
  PIPELINE_STATUSES = %w[
    not-started ready in-progress valid needs-review invalidated blocked
  ].freeze
  PIPELINE_LAYERS = %w[world character story outline prose editor].freeze
  LOOP_KEYS = %w[
    material population_care economic institutional knowledge meaning_identity
  ].freeze
  FACET_IDS = (1..22).map { |number| format("F%02d", number) }.freeze
  CHAIN_IDS = (1..5).map { |number| format("C%02d", number) }.freeze
  TEST_IDS = (1..12).map { |number| format("T%02d", number) }.freeze

  FACET_NAMES = {
    "F01" => "本体法则与不可行域",
    "F02" => "地理、生态与气候",
    "F03" => "资源、承载力与城市代谢",
    "F04" => "技术、魔法与基础设施",
    "F05" => "故障、维修与韧性",
    "F06" => "人口结构与生命历程",
    "F07" => "家庭、亲属与照护",
    "F08" => "身体、医疗、残障与死亡",
    "F09" => "劳动、职业与技能传承",
    "F10" => "住房、消费与日常时间",
    "F11" => "财产、货币、信用、债务与供应链",
    "F12" => "正式制度、非正式制度与组织政治",
    "F13" => "行政能力、执行裁量与合法性",
    "F14" => "法律、证据、申诉与多法域",
    "F15" => "阶层、地位、身份与社会边界",
    "F16" => "战争、边境、迁徙与外部关系",
    "F17" => "知识、教育、档案与谣言",
    "F18" => "语言、语域、命名与翻译",
    "F19" => "宗教、仪式、禁忌与道德经济",
    "F20" => "情绪规则、身体经验与物质文化",
    "F21" => "历史沉积与路径依赖",
    "F22" => "网络、集体行动、涌现与反馈"
  }.freeze

  LOOP_NAMES = {
    "material" => "物质再生产",
    "population_care" => "人口与照护再生产",
    "economic" => "经济再生产",
    "institutional" => "制度再生产",
    "knowledge" => "知识再生产",
    "meaning_identity" => "意义与身份再生产"
  }.freeze

  CHAIN_NAMES = {
    "C01" => "权利链",
    "C02" => "技术链",
    "C03" => "身份链",
    "C04" => "证据链",
    "C05" => "分配链"
  }.freeze

  ROUTES = {
    "worldbuilding-engine" => {
      "skill" => "worldbuilding-engine",
      "context_fields" => %w[authority dependencies change_log audit]
    },
    "world" => {
      "skill" => "fiction-core-zh:world-architect",
      "context_fields" => %w[authority premise knowledge_layers rules reproduction_loops facets coupling_chains]
    },
    "character" => {
      "skill" => "fiction-core-zh:character-architect",
      "context_fields" => %w[authority premise knowledge_layers rules places institutions history]
    },
    "story" => {
      "skill" => "fiction-core-zh:story-architect",
      "context_fields" => %w[authority premise rules actors places institutions history]
    },
    "outline" => {
      "skill" => "fiction-core-zh:outline-planner",
      "context_fields" => %w[authority actors places institutions history fiction_core]
    },
    "prose" => {
      "skill" => "fiction-core-zh:scene-prose-writer",
      "context_fields" => %w[authority knowledge_layers actors places fiction_core]
    },
    "editor" => {
      "skill" => "fiction-core-zh:story-editor",
      "context_fields" => %w[authority fiction_core change_log audit]
    }
  }.freeze

  class EngineError < StandardError; end

  module_function

  def deep_copy(value)
    JSON.parse(JSON.generate(value))
  end

  def read_json(path)
    raw = path == "-" ? $stdin.read : File.read(path, encoding: "UTF-8")
    JSON.parse(raw)
  rescue Errno::ENOENT
    raise EngineError, "找不到状态文件：#{path}"
  rescue JSON::ParserError => e
    raise EngineError, "JSON 无法解析：#{e.message}"
  end

  def atomic_write(path, content)
    directory = File.dirname(File.expand_path(path))
    FileUtils.mkdir_p(directory)
    temporary = File.join(directory, ".#{File.basename(path)}.#{Process.pid}.tmp")
    File.write(temporary, content, mode: "w", encoding: "UTF-8")
    File.rename(temporary, path)
  ensure
    File.delete(temporary) if defined?(temporary) && temporary && File.exist?(temporary)
  end

  def slug_id(title)
    ascii = title.to_s.downcase.gsub(/[^a-z0-9]+/, "-").gsub(/\A-|\-\z/, "")
    suffix = ascii.empty? ? SecureRandom.hex(4) : ascii
    "WORLD-#{suffix}"
  end

  def template(title: "未命名世界", seed: "", language: "zh-CN")
    state = JSON.parse(File.read(TEMPLATE_PATH, encoding: "UTF-8"))
    now = Time.now.utc.iso8601
    state["engine_version"] = VERSION
    state["project"]["id"] = slug_id(title)
    state["project"]["title"] = title
    state["project"]["seed"] = seed
    state["project"]["language"] = language
    state["project"]["created_at"] = now
    state["project"]["updated_at"] = now
    state
  end

  class Validator
    attr_reader :state, :errors, :warnings

    def initialize(state)
      @state = state
      @errors = []
      @warnings = []
      @ids = {}
    end

    def run
      unless state.is_a?(Hash)
        errors << "根节点必须是 JSON object"
        return result
      end

      check_top_level
      check_project
      check_authority
      check_premise
      check_knowledge_layers
      check_rules
      check_loops
      check_facets
      check_chains
      check_situated_tests
      check_pressure_tests
      check_entities
      check_pipeline
      check_dependencies
      check_change_log

      result
    end

    private

    def result
      {
        "valid" => errors.empty?,
        "errors" => errors.uniq,
        "warnings" => warnings.uniq,
        "stats" => {
          "rules" => array_at("rules").length,
          "facets" => array_at("facets").length,
          "pressure_tests" => array_at("pressure_tests").length,
          "entities" => %w[actors places institutions history].sum { |key| array_at(key).length },
          "dependencies" => array_at("dependencies").length
        }
      }
    end

    def check_top_level
      missing = TOP_LEVEL_KEYS - state.keys
      extra = state.keys - TOP_LEVEL_KEYS
      errors << "缺少顶层字段：#{missing.join(', ')}" unless missing.empty?
      warnings << "未知顶层字段：#{extra.join(', ')}；请放入 extensions" unless extra.empty?
      errors << "schema_version 必须是 #{SCHEMA_VERSION}" unless state["schema_version"] == SCHEMA_VERSION
    end

    def check_project
      project = hash_at("project")
      require_keys(project, %w[id title language seed mode status created_at updated_at], "project")
      register_id(project["id"], "project.id")
      errors << "project.title 必须是字符串" unless project["title"].is_a?(String)
      errors << "project.seed 必须是字符串" unless project["seed"].is_a?(String)
      warnings << "创意种子为空" if project["seed"].to_s.strip.empty?
      errors << "project.mode 无效" unless %w[create expand audit repair promote export].include?(project["mode"])
      errors << "project.status 无效" unless %w[developing review stable archived].include?(project["status"])
    end

    def check_authority
      authority = hash_at("authority")
      required = %w[source_of_truth read_only constraints locked_decisions author_required open_questions]
      require_keys(authority, required, "authority")
      %w[source_of_truth read_only constraints].each do |key|
        check_string_array(authority[key], "authority.#{key}")
      end
      %w[locked_decisions author_required open_questions].each do |key|
        decisions = authority[key]
        unless decisions.is_a?(Array)
          errors << "authority.#{key} 必须是数组"
          next
        end
        decisions.each_with_index do |decision, index|
          path = "authority.#{key}[#{index}]"
          check_decision(decision, path)
          if key == "author_required" && decision.is_a?(Hash) && decision["status"] != "author-required"
            errors << "#{path}.status 必须是 author-required"
          end
        end
      end
    end

    def check_decision(decision, path)
      unless decision.is_a?(Hash)
        errors << "#{path} 必须是 object"
        return
      end
      require_keys(decision, %w[id question status evidence], path)
      register_id(decision["id"], "#{path}.id")
      check_authority_status(decision["status"], "#{path}.status")
      check_string_array(decision["evidence"], "#{path}.evidence")
      if %w[canon proposed].include?(decision["status"]) && Array(decision["evidence"]).empty?
        errors << "#{path} 为 #{decision['status']}，必须有 evidence"
      end
    end

    def check_premise
      premise = hash_at("premise")
      require_keys(premise, %w[status core_difference human_experience scale aesthetic_surface themes evidence], "premise")
      check_authority_status(premise["status"], "premise.status")
      %w[core_difference human_experience scale].each do |key|
        errors << "premise.#{key} 必须是字符串" unless premise[key].is_a?(String)
      end
      %w[aesthetic_surface themes evidence].each do |key|
        check_string_array(premise[key], "premise.#{key}")
      end
      if %w[proposed canon].include?(premise["status"])
        %w[core_difference human_experience scale].each do |key|
          errors << "premise.#{key} 不能为空" if premise[key].to_s.strip.empty?
        end
      end
      if premise["status"] == "canon" && Array(premise["evidence"]).empty?
        errors << "canon premise 必须有 evidence"
      end
    end

    def check_knowledge_layers
      layers = hash_at("knowledge_layers")
      keys = %w[author_truth expert_models public_beliefs reader_unknowns]
      require_keys(layers, keys, "knowledge_layers")
      keys.each do |key|
        entries = layers[key]
        unless entries.is_a?(Array)
          errors << "knowledge_layers.#{key} 必须是数组"
          next
        end
        entries.each_with_index do |entry, index|
          path = "knowledge_layers.#{key}[#{index}]"
          unless entry.is_a?(Hash)
            errors << "#{path} 必须是 object"
            next
          end
          require_keys(entry, %w[id claim status known_by evidence], path)
          register_id(entry["id"], "#{path}.id")
          check_authority_status(entry["status"], "#{path}.status")
          check_string_array(entry["known_by"], "#{path}.known_by")
          check_string_array(entry["evidence"], "#{path}.evidence")
        end
      end
    end

    def check_rules
      rules = array_at("rules")
      required = %w[
        id name status capability impossibility inputs outputs costs losses access visibility
        scale_limits failure_modes maintenance countermeasures knowledge_layer dependencies evidence
      ]
      rules.each_with_index do |rule, index|
        path = "rules[#{index}]"
        unless rule.is_a?(Hash)
          errors << "#{path} 必须是 object"
          next
        end
        require_keys(rule, required, path)
        register_id(rule["id"], "#{path}.id")
        check_authority_status(rule["status"], "#{path}.status")
        %w[capability impossibility].each do |key|
          errors << "#{path}.#{key} 必须是字符串" unless rule[key].is_a?(String)
        end
        list_keys = %w[
          inputs outputs costs losses access visibility scale_limits failure_modes maintenance
          countermeasures dependencies evidence
        ]
        list_keys.each { |key| check_string_array(rule[key], "#{path}.#{key}") }
        unless %w[author_truth expert_model public_belief mixed unknown].include?(rule["knowledge_layer"])
          errors << "#{path}.knowledge_layer 无效"
        end

        next if rule["status"] == "deprecated"

        strict = %w[proposed canon].include?(rule["status"])
        %w[capability impossibility].each do |key|
          message = "#{path}.#{key} 为空"
          strict ? errors << message : warnings << message if rule[key].to_s.strip.empty?
        end
        %w[costs failure_modes maintenance].each do |key|
          message = "#{path}.#{key} 为空，规则账本未闭合"
          strict ? errors << message : warnings << message if Array(rule[key]).empty?
        end
        if rule["status"] == "canon" && Array(rule["evidence"]).empty?
          errors << "#{path} 为 canon，必须有 evidence"
        end
      end
    end

    def check_loops
      loops = hash_at("reproduction_loops")
      missing = LOOP_KEYS - loops.keys
      errors << "reproduction_loops 缺少：#{missing.join(', ')}" unless missing.empty?
      LOOP_KEYS.each do |key|
        check_coverage_entry(loops[key], "reproduction_loops.#{key}") if loops.key?(key)
      end
    end

    def check_facets
      facets = array_at("facets")
      facets.each_with_index do |facet, index|
        path = "facets[#{index}]"
        unless facet.is_a?(Hash)
          errors << "#{path} 必须是 object"
          next
        end
        require_keys(facet, %w[id name status maturity evidence gaps dependencies reason], path)
        register_id(facet["id"], "#{path}.id")
        check_coverage_status(facet["status"], "#{path}.status")
        %w[evidence gaps dependencies].each { |key| check_string_array(facet[key], "#{path}.#{key}") }
        maturity = facet["maturity"]
        unless maturity.is_a?(Hash) && %w[framework instance].all? { |key| maturity[key].is_a?(Integer) && maturity[key].between?(0, 6) }
          errors << "#{path}.maturity 必须含 0..6 的 framework 与 instance"
        end
        check_coverage_evidence(facet, path)
      end
      actual = facets.map { |facet| facet["id"] if facet.is_a?(Hash) }.compact
      missing = FACET_IDS - actual
      extra = actual - FACET_IDS
      errors << "facets 缺少标准方面：#{missing.join(', ')}" unless missing.empty?
      warnings << "facets 含扩展 ID：#{extra.join(', ')}；建议放入 extensions" unless extra.empty?
    end

    def check_chains
      chains = array_at("coupling_chains")
      chains.each_with_index do |chain, index|
        path = "coupling_chains[#{index}]"
        unless chain.is_a?(Hash)
          errors << "#{path} 必须是 object"
          next
        end
        require_keys(chain, %w[id name status nodes breaks evidence reason], path)
        register_id(chain["id"], "#{path}.id")
        check_coverage_status(chain["status"], "#{path}.status")
        %w[nodes breaks evidence].each { |key| check_string_array(chain[key], "#{path}.#{key}") }
        check_coverage_evidence(chain, path)
      end
      actual = chains.map { |chain| chain["id"] if chain.is_a?(Hash) }.compact
      missing = CHAIN_IDS - actual
      errors << "coupling_chains 缺少：#{missing.join(', ')}" unless missing.empty?
    end

    def check_situated_tests
      tests = hash_at("situated_tests")
      keys = %w[ordinary_tuesday seven_day_failure life_course ten_year_feedback]
      missing = keys - tests.keys
      errors << "situated_tests 缺少：#{missing.join(', ')}" unless missing.empty?
      keys.each do |key|
        entry = tests[key]
        next unless entry
        path = "situated_tests.#{key}"
        unless entry.is_a?(Hash)
          errors << "#{path} 必须是 object"
          next
        end
        require_keys(entry, %w[status scenario actors evidence contradictions reason], path)
        check_coverage_status(entry["status"], "#{path}.status")
        %w[actors evidence contradictions].each { |field| check_string_array(entry[field], "#{path}.#{field}") }
        check_coverage_evidence(entry, path, text_field: "scenario")
      end
    end

    def check_pressure_tests
      tests = array_at("pressure_tests")
      tests.each_with_index do |test, index|
        path = "pressure_tests[#{index}]"
        unless test.is_a?(Hash)
          errors << "#{path} 必须是 object"
          next
        end
        require_keys(test, %w[id name status result evidence failures], path)
        register_id(test["id"], "#{path}.id")
        errors << "#{path}.status 无效" unless PRESSURE_STATUSES.include?(test["status"])
        %w[evidence failures].each { |key| check_string_array(test[key], "#{path}.#{key}") }
        if test["status"] != "not-run" && test["result"].to_s.strip.empty?
          errors << "#{path} 已运行但 result 为空"
        end
        if %w[pass mixed].include?(test["status"]) && Array(test["evidence"]).empty?
          errors << "#{path} 为 #{test['status']}，必须有 evidence"
        end
      end
      actual = tests.map { |test| test["id"] if test.is_a?(Hash) }.compact
      missing = TEST_IDS - actual
      errors << "pressure_tests 缺少：#{missing.join(', ')}" unless missing.empty?
    end

    def check_entities
      %w[actors places institutions history].each do |key|
        entries = array_at(key)
        entries.each_with_index do |entry, index|
          path = "#{key}[#{index}]"
          unless entry.is_a?(Hash)
            errors << "#{path} 必须是 object"
            next
          end
          require_keys(entry, %w[id name status summary evidence], path)
          register_id(entry["id"], "#{path}.id")
          check_authority_status(entry["status"], "#{path}.status")
          check_string_array(entry["evidence"], "#{path}.evidence")
          if entry["status"] == "canon" && Array(entry["evidence"]).empty?
            errors << "#{path} 为 canon，必须有 evidence"
          end
        end
      end
    end

    def check_pipeline
      pipeline = hash_at("fiction_core")
      missing = PIPELINE_LAYERS - pipeline.keys
      errors << "fiction_core 缺少：#{missing.join(', ')}" unless missing.empty?
      PIPELINE_LAYERS.each do |layer|
        entry = pipeline[layer]
        next unless entry
        path = "fiction_core.#{layer}"
        unless entry.is_a?(Hash)
          errors << "#{path} 必须是 object"
          next
        end
        require_keys(entry, %w[status artifacts invalidated_by notes], path)
        errors << "#{path}.status 无效" unless PIPELINE_STATUSES.include?(entry["status"])
        %w[artifacts invalidated_by notes].each { |key| check_string_array(entry[key], "#{path}.#{key}") }
      end

      PIPELINE_LAYERS.each_with_index do |layer, index|
        entry = pipeline[layer]
        next unless entry.is_a?(Hash) && %w[invalidated needs-review].include?(entry["status"])
        PIPELINE_LAYERS[(index + 1)..]&.each do |downstream|
          next if downstream == "editor"
          if pipeline.dig(downstream, "status") == "valid"
            errors << "#{layer} 已失效或待复核，但下游 #{downstream} 仍标为 valid"
          end
        end
      end
    end

    def check_dependencies
      dependencies = array_at("dependencies")
      dependencies.each_with_index do |edge, index|
        path = "dependencies[#{index}]"
        unless edge.is_a?(Hash)
          errors << "#{path} 必须是 object"
          next
        end
        require_keys(edge, %w[from to kind status], path)
        unless %w[requires informs derives contradicts].include?(edge["kind"])
          errors << "#{path}.kind 无效"
        end
        unless %w[active proposed deprecated].include?(edge["status"])
          errors << "#{path}.status 无效"
        end
      end

      dependencies.each_with_index do |edge, index|
        next unless edge.is_a?(Hash)
        %w[from to].each do |side|
          reference = edge[side]
          next if @ids.key?(reference)
          next if reference.to_s.include?("/") || reference.to_s.end_with?(".md", ".json")
          warnings << "dependencies[#{index}].#{side} 未解析：#{reference}"
        end
      end
    end

    def check_change_log
      logs = array_at("change_log")
      logs.each_with_index do |entry, index|
        path = "change_log[#{index}]"
        unless entry.is_a?(Hash)
          errors << "#{path} 必须是 object"
          next
        end
        require_keys(entry, %w[id at summary source authority changed_ids invalidated_layers], path)
        register_id(entry["id"], "#{path}.id")
        check_authority_status(entry["authority"], "#{path}.authority")
        %w[changed_ids invalidated_layers].each { |key| check_string_array(entry[key], "#{path}.#{key}") }
      end
    end

    def check_coverage_entry(entry, path)
      unless entry.is_a?(Hash)
        errors << "#{path} 必须是 object"
        return
      end
      require_keys(entry, %w[status chain evidence gaps reason], path)
      check_coverage_status(entry["status"], "#{path}.status")
      %w[chain evidence gaps].each { |key| check_string_array(entry[key], "#{path}.#{key}") }
      check_coverage_evidence(entry, path, text_field: "chain")
    end

    def check_coverage_evidence(entry, path, text_field: nil)
      status = entry["status"]
      evidence = Array(entry["evidence"])
      if status == "covered" && evidence.empty?
        errors << "#{path} 为 covered，必须有 evidence"
      end
      if status == "not-applicable" && entry["reason"].to_s.strip.empty?
        errors << "#{path} 为 not-applicable，必须写 reason"
      end
      if status == "partial" && evidence.empty? && (text_field.nil? || Array(entry[text_field]).empty? || entry[text_field].to_s.strip.empty?)
        warnings << "#{path} 为 partial，但没有证据或内容"
      end
      maturity = entry["maturity"]
      if maturity.is_a?(Hash) && maturity.values.any? { |value| value.to_i.positive? } && evidence.empty?
        errors << "#{path} 声明成熟度大于 L0，必须有 evidence"
      end
    end

    def check_authority_status(value, path)
      errors << "#{path} 权威状态无效：#{value.inspect}" unless AUTHORITY_STATUSES.include?(value)
    end

    def check_coverage_status(value, path)
      errors << "#{path} 覆盖状态无效：#{value.inspect}" unless COVERAGE_STATUSES.include?(value)
    end

    def check_string_array(value, path)
      unless value.is_a?(Array) && value.all? { |item| item.is_a?(String) }
        errors << "#{path} 必须是字符串数组"
      end
    end

    def register_id(value, path)
      unless value.is_a?(String) && value.match?(/\A[A-Za-z0-9][A-Za-z0-9._:\/-]*\z/)
        errors << "#{path} 不是有效 ID"
        return
      end
      if @ids.key?(value)
        errors << "ID 重复：#{value}（#{@ids[value]} 与 #{path}）"
      else
        @ids[value] = path
      end
    end

    def require_keys(object, keys, path)
      unless object.is_a?(Hash)
        errors << "#{path} 必须是 object"
        return
      end
      missing = keys - object.keys
      errors << "#{path} 缺少字段：#{missing.join(', ')}" unless missing.empty?
    end

    def hash_at(key)
      value = state[key]
      return value if value.is_a?(Hash)
      errors << "#{key} 必须是 object"
      {}
    end

    def array_at(key)
      value = state[key]
      return value if value.is_a?(Array)
      errors << "#{key} 必须是数组" if state.key?(key)
      []
    end
  end

  class Auditor
    attr_reader :state, :validation

    def initialize(state)
      @state = state
      @validation = Validator.new(state).run
    end

    def run
      rules = Array(state["rules"]).reject { |rule| rule.is_a?(Hash) && rule["status"] == "deprecated" }
      ready_rules = rules.select { |rule| rule_ready?(rule) }
      loops = state["reproduction_loops"].is_a?(Hash) ? state["reproduction_loops"] : {}
      facets = Array(state["facets"]).select { |facet| facet.is_a?(Hash) }
      chains = Array(state["coupling_chains"]).select { |chain| chain.is_a?(Hash) }
      situated = state["situated_tests"].is_a?(Hash) ? state["situated_tests"] : {}
      pressure = Array(state["pressure_tests"]).select { |test| test.is_a?(Hash) }
      premise = state["premise"].is_a?(Hash) ? state["premise"] : {}

      blocking = []
      blocking.concat(validation["errors"].map { |error| "结构：#{error}" })
      %w[core_difference human_experience scale].each do |key|
        blocking << "premise.#{key} 尚未建立" if premise[key].to_s.strip.empty?
      end
      blocking << "尚无核心规则" if rules.empty?
      if rules.any? && ready_rules.empty?
        blocking << "核心规则尚未同时闭合允许／禁止、成本、故障和维护"
      end

      gap_loops = LOOP_KEYS.select { |key| loops.dig(key, "status") == "gap" || loops[key].nil? }
      gap_facets = facets.select { |facet| facet["status"] == "gap" }
      gap_chains = chains.select { |chain| chain["status"] == "gap" }
      gap_situated = situated.select { |_key, entry| entry.is_a?(Hash) && entry["status"] == "gap" }.keys
      unrun_pressure = pressure.select { |test| test["status"] == "not-run" }
      failed_pressure = pressure.select { |test| %w[fail mixed].include?(test["status"]) }

      high_leverage = []
      high_leverage << "先把核心差异、体验承诺与尺度压成 premise" if premise.values_at("core_difference", "human_experience", "scale").any? { |value| value.to_s.strip.empty? }
      high_leverage << "建立至少一条带不可行域、成本、故障和维护的核心规则" if ready_rules.empty?
      unless gap_loops.empty?
        names = gap_loops.first(3).map { |key| LOOP_NAMES[key] }
        high_leverage << "闭合缺失的再生产循环：#{names.join('、')}#{'等' if gap_loops.length > 3}"
      end
      unless gap_facets.empty?
        names = gap_facets.first(5).map { |facet| facet["name"].to_s.empty? ? FACET_NAMES[facet["id"]] : facet["name"] }
        high_leverage << "优先补二十二面缺口：#{names.compact.join('、')}#{'等' if gap_facets.length > 5}"
      end
      high_leverage << "走通至少一条完整耦合链，防止孤立词条" unless gap_chains.empty?
      high_leverage << "写一个普通星期二和一次七日故障，检验同一实例" if gap_situated.include?("ordinary_tuesday") || gap_situated.include?("seven_day_failure")
      high_leverage << "运行主角移除、最贫者、维修与十年后等压力测试" unless unrun_pressure.empty?

      framework_levels = facets.map { |facet| facet.dig("maturity", "framework").to_i }
      instance_levels = facets.map { |facet| facet.dig("maturity", "instance").to_i }
      framework_maturity = maturity_summary(framework_levels)
      instance_maturity = maturity_summary(instance_levels)
      iteration = iteration_summary(framework_maturity, instance_maturity)

      if iteration["saturation"] == "framework-ahead"
        high_leverage.unshift("停止横向填表；选择一个共用地图、机构、家庭与时间分母的纵切")
      end
      if iteration["checkpoint_due"]
        high_leverage.unshift("本轮到达全量检查点；完成定向检查后运行项目全量门禁")
      end

      result = {
        "engine_version" => VERSION,
        "validation" => validation,
        "gates" => {
          "foundation" => validation["valid"] && blocking.none? { |item| item.start_with?("premise") || item.include?("核心规则") || item.start_with?("结构") },
          "social_realism" => gap_loops.empty? && gap_facets.empty? && gap_chains.empty?,
          "situated_reality" => gap_situated.empty?,
          "counterfactual" => unrun_pressure.empty? && failed_pressure.empty?
        },
        "rules" => {
          "active" => rules.length,
          "ledger_ready" => ready_rules.length,
          "incomplete_ids" => rules.reject { |rule| rule_ready?(rule) }.map { |rule| rule["id"] }
        },
        "reproduction_loops" => coverage_summary(loops.map { |key, entry| [key, entry] }),
        "facets" => coverage_summary(facets.map { |facet| [facet["id"], facet] }).merge(
          "framework_maturity" => framework_maturity,
          "instance_maturity" => instance_maturity
        ),
        "coupling_chains" => coverage_summary(chains.map { |chain| [chain["id"], chain] }),
        "situated_tests" => coverage_summary(situated.map { |key, entry| [key, entry] }),
        "pressure_tests" => {
          "pass" => pressure.count { |test| test["status"] == "pass" },
          "mixed" => pressure.count { |test| test["status"] == "mixed" },
          "fail" => pressure.count { |test| test["status"] == "fail" },
          "not_run" => unrun_pressure.length,
          "failed_ids" => failed_pressure.map { |test| test["id"] }
        },
        "iteration" => iteration,
        "blocking_gaps" => blocking.uniq,
        "high_leverage_actions" => high_leverage.uniq.first(8),
        "warnings" => [
          "机器审计只证明结构与已登记证据，不替代语义、事实或文学审查。",
          "通用框架成熟度与具体地区实例成熟度必须分开解释。"
        ] + validation["warnings"],
        "route" => Router.new(state, validation: validation).run
      }
      result
    end

    private

    def rule_ready?(rule)
      rule.is_a?(Hash) &&
        !rule["capability"].to_s.strip.empty? &&
        !rule["impossibility"].to_s.strip.empty? &&
        !Array(rule["costs"]).empty? &&
        !Array(rule["failure_modes"]).empty? &&
        !Array(rule["maintenance"]).empty?
    end

    def coverage_summary(pairs)
      summary = COVERAGE_STATUSES.to_h { |status| [status.tr("-", "_"), 0] }
      gap_ids = []
      pairs.each do |id, entry|
        status = entry.is_a?(Hash) ? entry["status"] : "gap"
        key = COVERAGE_STATUSES.include?(status) ? status.tr("-", "_") : "gap"
        summary[key] += 1
        gap_ids << id if status == "gap"
      end
      summary["gap_ids"] = gap_ids
      summary
    end

    def maturity_summary(levels)
      return { "minimum" => 0, "median" => 0, "maximum" => 0, "histogram" => {} } if levels.empty?
      sorted = levels.sort
      histogram = (0..6).to_h { |level| ["L#{level}", levels.count(level)] }
      {
        "minimum" => sorted.first,
        "median" => sorted[sorted.length / 2],
        "maximum" => sorted.last,
        "histogram" => histogram
      }
    end

    def iteration_summary(framework, instance)
      extensions = state["extensions"].is_a?(Hash) ? state["extensions"] : {}
      raw = extensions["iteration"]
      tracked = raw.is_a?(Hash)
      data = tracked ? raw : {}
      round = nonnegative_integer(data["round"])
      checkpoint_every = nonnegative_integer(data["checkpoint_every"])
      checkpoint_every = 3 if checkpoint_every <= 0
      last_checkpoint = nonnegative_integer(data["last_checkpoint_round"])
      immediate_reasons = []
      immediate_reasons << "authority-promotion" if data["promotion_requested"] == true
      immediate_reasons << "contract-change" if data["contract_changed"] == true
      immediate_reasons << "shared-merge" if data["shared_merge_pending"] == true
      cadence_due = tracked && round.positive? && round - last_checkpoint >= checkpoint_every
      framework_ahead = framework["median"] >= 3 && framework["median"] - instance["median"] >= 2
      scope = data["persistence_scope"].to_s
      scope = "conversation-only" unless %w[conversation-only candidate-files canon-files].include?(scope)

      {
        "tracked" => tracked,
        "goal" => data["goal"].to_s,
        "persistence_scope" => scope,
        "round" => round,
        "active_slice" => data["active_slice"].to_s,
        "checkpoint_every" => checkpoint_every,
        "last_checkpoint_round" => last_checkpoint,
        "checkpoint_due" => cadence_due || !immediate_reasons.empty?,
        "checkpoint_reasons" => immediate_reasons + (cadence_due ? ["cadence"] : []),
        "saturation" => framework_ahead ? "framework-ahead" : "balanced-or-early"
      }
    end

    def nonnegative_integer(value)
      return [value, 0].max if value.is_a?(Integer)
      return value.to_i if value.is_a?(String) && value.match?(/\A\d+\z/)

      0
    end
  end

  class Router
    def initialize(state, validation: nil)
      @state = state
      @validation = validation || Validator.new(state).run
    end

    def run
      return route_for("worldbuilding-engine", "状态结构或不变量未通过，先修复工程状态") unless @validation["valid"]

      pipeline = @state["fiction_core"].is_a?(Hash) ? @state["fiction_core"] : {}
      PIPELINE_LAYERS.each do |layer|
        status = pipeline.dig(layer, "status")
        if %w[invalidated needs-review].include?(status)
          return route_for(layer, "#{layer} 层状态为 #{status}，应由该所有权层复核")
        end
      end

      %w[world character story outline].each do |layer|
        status = pipeline.dig(layer, "status")
        return route_for(layer, "#{layer} 层尚未达到 valid（当前：#{status || 'missing'}）") unless status == "valid"
      end

      prose_status = pipeline.dig("prose", "status")
      return route_for("prose", "已有有效 Scene Contract，可进入或继续正文") unless prose_status == "valid"

      route_for("editor", "世界、人物、故事、细纲和正文均标为 valid，进入单模式审查")
    end

    private

    def route_for(key, reason)
      route = ROUTES.fetch(key)
      {
        "owner_layer" => key,
        "skill" => route["skill"],
        "reason" => reason,
        "context_fields" => route["context_fields"]
      }
    end
  end

  class Invalidator
    DOWNSTREAM = {
      "world" => %w[character story outline prose],
      "character" => %w[story outline prose],
      "story" => %w[outline prose],
      "outline" => %w[prose],
      "prose" => [],
      "editor" => []
    }.freeze

    def initialize(state, from:, reason:, hard: false)
      @state = state
      @from = from
      @reason = reason
      @hard = hard
    end

    def run
      raise EngineError, "无效层级：#{@from}" unless PIPELINE_LAYERS.include?(@from)
      raise EngineError, "失效原因不能为空" if @reason.to_s.strip.empty?

      state = WorldbuildingEngine.deep_copy(@state)
      pipeline = state.fetch("fiction_core")
      change_id = "CHG-#{Time.now.utc.strftime('%Y%m%dT%H%M%SZ')}-#{SecureRandom.hex(2)}"
      targets = DOWNSTREAM.fetch(@from)
      target_status = @hard ? "invalidated" : "needs-review"

      targets.each do |layer|
        entry = pipeline.fetch(layer)
        entry["status"] = target_status unless entry["status"] == "blocked" && !@hard
        entry["invalidated_by"] << change_id unless entry["invalidated_by"].include?(change_id)
        entry["notes"] << @reason unless entry["notes"].include?(@reason)
      end

      now = Time.now.utc.iso8601
      state["project"]["updated_at"] = now
      state["change_log"] << {
        "id" => change_id,
        "at" => now,
        "summary" => @reason,
        "source" => @from,
        "authority" => "draft",
        "changed_ids" => [],
        "invalidated_layers" => targets
      }
      state
    end
  end

  def parse_common_json_flag(argv)
    options = { json: false }
    parser = OptionParser.new do |opts|
      opts.on("--json", "输出 JSON") { options[:json] = true }
    end
    parser.parse!(argv)
    [options, parser]
  end

  def print_json(value)
    puts JSON.pretty_generate(value)
  end

  def print_validation(result)
    puts(result["valid"] ? "VALID" : "INVALID")
    puts "错误：#{result['errors'].length}；警告：#{result['warnings'].length}"
    result["errors"].each { |item| puts "ERROR #{item}" }
    result["warnings"].each { |item| puts "WARNING #{item}" }
    puts "统计：规则 #{result.dig('stats', 'rules')}，二十二面 #{result.dig('stats', 'facets')}，压力测试 #{result.dig('stats', 'pressure_tests')}，依赖 #{result.dig('stats', 'dependencies')}"
  end

  def print_audit(result)
    validation = result["validation"]
    puts validation["valid"] ? "结构门：通过" : "结构门：失败"
    gates = result["gates"]
    puts "基础门：#{gates['foundation'] ? '通过' : '未通过'}；社会真实门：#{gates['social_realism'] ? '通过' : '未通过'}；情境门：#{gates['situated_reality'] ? '通过' : '未通过'}；反事实门：#{gates['counterfactual'] ? '通过' : '未通过'}"
    puts "规则账本：#{result.dig('rules', 'ledger_ready')}/#{result.dig('rules', 'active')} 闭合"
    puts "再生产循环缺口：#{result.dig('reproduction_loops', 'gap')}；二十二面缺口：#{result.dig('facets', 'gap')}；五链缺口：#{result.dig('coupling_chains', 'gap')}"
    puts "通用成熟度：L#{result.dig('facets', 'framework_maturity', 'minimum')}—L#{result.dig('facets', 'framework_maturity', 'maximum')}；实例成熟度：L#{result.dig('facets', 'instance_maturity', 'minimum')}—L#{result.dig('facets', 'instance_maturity', 'maximum')}"
    if result.dig("iteration", "tracked")
      puts "迭代：第 #{result.dig('iteration', 'round')} 轮；持久化 #{result.dig('iteration', 'persistence_scope')}；全量检查点#{result.dig('iteration', 'checkpoint_due') ? '到期' : '未到期'}"
    end
    unless result["blocking_gaps"].empty?
      puts "阻断项："
      result["blocking_gaps"].each { |item| puts "- #{item}" }
    end
    unless result["high_leverage_actions"].empty?
      puts "高收益下一步："
      result["high_leverage_actions"].each { |item| puts "- #{item}" }
    end
    route = result["route"]
    puts "建议路由：#{route['skill']}（#{route['reason']}）"
    puts "注意：#{result['warnings'].first}"
  end

  def usage
    <<~TEXT
      Worldbuilding Engine #{VERSION}

      用法：
        worldbuild.rb template [--title TITLE] [--seed TEXT] [--language CODE]
        worldbuild.rb init DIR --title TITLE --seed TEXT [--language CODE]
        worldbuild.rb validate STATE.json [--json]
        worldbuild.rb audit STATE.json [--json]
        worldbuild.rb route STATE.json [--json]
        worldbuild.rb packet STATE.json [--json]
        worldbuild.rb invalidate STATE.json --from LAYER --reason TEXT [--hard] [--json]

      STATE.json 可用 - 表示从 stdin 读取。init 与 invalidate 是写操作；其余命令只读。
    TEXT
  end

  def run_cli(argv)
    command = argv.shift
    case command
    when "template"
      options = { title: "未命名世界", seed: "", language: "zh-CN" }
      OptionParser.new do |opts|
        opts.on("--title TITLE") { |value| options[:title] = value }
        opts.on("--seed TEXT") { |value| options[:seed] = value }
        opts.on("--language CODE") { |value| options[:language] = value }
      end.parse!(argv)
      print_json(template(**options))
      0
    when "init"
      directory = argv.shift
      raise EngineError, "init 需要明确项目目录" if directory.to_s.strip.empty?
      options = { title: nil, seed: nil, language: "zh-CN" }
      OptionParser.new do |opts|
        opts.on("--title TITLE") { |value| options[:title] = value }
        opts.on("--seed TEXT") { |value| options[:seed] = value }
        opts.on("--language CODE") { |value| options[:language] = value }
      end.parse!(argv)
      raise EngineError, "--title 不能为空" if options[:title].to_s.strip.empty?
      raise EngineError, "--seed 不能为空" if options[:seed].to_s.strip.empty?
      state_path = File.join(directory, "world-state.json")
      project_path = File.join(directory, "PROJECT.md")
      raise EngineError, "目标已含 world-state.json；拒绝覆盖" if File.exist?(state_path)
      FileUtils.mkdir_p(directory)
      state = template(title: options[:title], seed: options[:seed], language: options[:language])
      project = File.read(PROJECT_TEMPLATE_PATH, encoding: "UTF-8")
        .gsub("未命名世界工程", "#{options[:title]}世界工程")
        .sub("待填写。", options[:seed])
      atomic_write(state_path, JSON.pretty_generate(state) + "\n")
      atomic_write(project_path, project)
      puts "已创建：#{state_path}"
      puts "已创建：#{project_path}"
      0
    when "validate"
      path = argv.shift
      raise EngineError, "validate 需要状态文件或 -" if path.to_s.strip.empty?
      options, = parse_common_json_flag(argv)
      result = Validator.new(read_json(path)).run
      options[:json] ? print_json(result) : print_validation(result)
      result["valid"] ? 0 : 1
    when "audit"
      path = argv.shift
      raise EngineError, "audit 需要状态文件或 -" if path.to_s.strip.empty?
      options, = parse_common_json_flag(argv)
      result = Auditor.new(read_json(path)).run
      options[:json] ? print_json(result) : print_audit(result)
      result.dig("validation", "valid") ? 0 : 1
    when "route"
      path = argv.shift
      raise EngineError, "route 需要状态文件或 -" if path.to_s.strip.empty?
      options, = parse_common_json_flag(argv)
      state = read_json(path)
      result = Router.new(state).run
      if options[:json]
        print_json(result)
      else
        puts "#{result['skill']}"
        puts "原因：#{result['reason']}"
        puts "上下文：#{result['context_fields'].join(', ')}"
      end
      0
    when "packet"
      path = argv.shift
      raise EngineError, "packet 需要状态文件或 -" if path.to_s.strip.empty?
      options, = parse_common_json_flag(argv)
      state = read_json(path)
      audit = Auditor.new(state).run
      route = audit["route"]
      packet = {
        "project" => state["project"],
        "authority" => state["authority"],
        "premise" => state["premise"],
        "constraints" => state.dig("authority", "constraints"),
        "route" => route,
        "context" => route["context_fields"].to_h { |field| [field, state[field]] },
        "audit_summary" => {
          "gates" => audit["gates"],
          "blocking_gaps" => audit["blocking_gaps"],
          "high_leverage_actions" => audit["high_leverage_actions"],
          "iteration" => audit["iteration"]
        }
      }
      options[:json] ? print_json(packet) : puts(JSON.pretty_generate(packet))
      0
    when "invalidate"
      path = argv.shift
      raise EngineError, "invalidate 需要明确状态文件，不能使用 -" if path.to_s.strip.empty? || path == "-"
      options = { from: nil, reason: nil, hard: false, json: false }
      OptionParser.new do |opts|
        opts.on("--from LAYER") { |value| options[:from] = value }
        opts.on("--reason TEXT") { |value| options[:reason] = value }
        opts.on("--hard") { options[:hard] = true }
        opts.on("--json") { options[:json] = true }
      end.parse!(argv)
      state = read_json(path)
      updated = Invalidator.new(state, from: options[:from], reason: options[:reason], hard: options[:hard]).run
      validation = Validator.new(updated).run
      raise EngineError, "失效传播后状态无效：#{validation['errors'].join('; ')}" unless validation["valid"]
      atomic_write(path, JSON.pretty_generate(updated) + "\n")
      result = {
        "updated" => path,
        "from" => options[:from],
        "invalidated_layers" => updated["change_log"].last["invalidated_layers"],
        "change_id" => updated["change_log"].last["id"]
      }
      options[:json] ? print_json(result) : puts("已传播失效：#{result['invalidated_layers'].join(', ')}（#{result['change_id']}）")
      0
    when "help", "--help", "-h", nil
      puts usage
      command.nil? ? 1 : 0
    else
      raise EngineError, "未知命令：#{command}\n#{usage}"
    end
  rescue OptionParser::ParseError => e
    warn "ERROR #{e.message}"
    2
  rescue EngineError => e
    warn "ERROR #{e.message}"
    2
  end
end

exit(WorldbuildingEngine.run_cli(ARGV)) if $PROGRAM_NAME == __FILE__
