#!/usr/bin/env ruby

require "fileutils"
require "json"
require "minitest/autorun"
require "tmpdir"
load File.expand_path("worldcheck", __dir__)

class WorldcheckTest < Minitest::Test
  def setup
    @tmp = Dir.mktmpdir("worldcheck-test")
    @root = File.join(@tmp, "project")
    @content = File.join(@root, "worldbook")
    @policies = File.join(@root, "policies")
    @scripts = File.join(@root, "scripts")
    FileUtils.mkdir_p([@content, @policies, @scripts])
    write_json("policies/canon-rules.json", {"rules" => []})
    write_json("policies/design-principles.json", {
      "required_for_all" => ["PHI-01"],
      "principles" => [{"id" => "PHI-01", "title" => "守恒", "question" => "账本是否闭合？"}],
      "scopes" => []
    })
    write_json("policies/physics.json", {"claims" => []})
    write_json("policies/dependencies.json", {
      "edge_semantics" => "A -> B means B depends on A",
      "core_settings" => ["Alpha"],
      "edges" => {"Alpha" => ["Beta"]}
    })
    File.write(File.join(@scripts, "gate.sh"), <<~SH)
      echo run >> scripts/gate-count
      if [ -e scripts/fail ]; then
        echo '[SUMMARY] errors=1 warnings=0'
        exit 1
      fi
      echo '[SUMMARY] errors=0 warnings=0'
    SH
    page("lore/Alpha.md", "Alpha", "# Alpha\nold\n", aliases: ["A"])
    page("lore/Beta.md", "Beta", "# Beta\ndependent\n")
    page("lore/Gamma.md", "Gamma", "# Gamma\nsee [[Alpha]]\n")
    write_config
    @project = Worldcheck::Project.load(config_path)
    @state_root = File.join(@tmp, "state")
    @app = Worldcheck::App.new(@project, @state_root)
    code, result = @app.check([], full: true)
    assert_equal 0, code, result.to_json
  end

  def teardown
    FileUtils.remove_entry(@tmp) if File.exist?(@tmp)
  end

  def test_host_configured_state_directory
    previous = ENV["XDG_STATE_HOME"]
    ENV["XDG_STATE_HOME"] = File.join(@tmp, "portable-state")
    assert_equal File.join(@tmp, "portable-state", "worldcheck", "portable-project"), Worldcheck::Store.new("portable-project").root
    ENV["XDG_STATE_HOME"] = "relative"
    assert_raises(Worldcheck::Failure) { Worldcheck::Store.new("portable-project") }
  ensure
    previous ? ENV["XDG_STATE_HOME"] = previous : ENV.delete("XDG_STATE_HOME")
  end

  def test_safe_frontmatter_rejects_object_tags_and_aliases
    ["injected: !ruby/object:Object {}", "left: &value test\nright: *value"].each do |unsafe|
      text = frontmatter("Alpha").sub("related: []", unsafe) + "# Alpha\nunsafe data\n"
      File.write(page_path("Alpha.md"), text)
      code, result = @app.check([], full: true)
      assert_equal 1, code
      assert result["issues"].any? { |item| item["code"] == "frontmatter-invalid" }
    end
  end

  def test_full_gate_failure_does_not_replace_checkpoint
    before = File.read(File.join(@state_root, "state.json"))
    File.write(File.join(@scripts, "fail"), "1")
    code, payload = @app.check([], full: true)
    assert_equal 1, code
    assert_equal "full-gate-failed", payload["issues"].first["code"]
    assert_equal before, File.read(File.join(@state_root, "state.json"))
  end

  def test_change_dependency_and_backlink_packet_without_full_gate
    page("lore/Alpha.md", "Alpha", "# Alpha\nnew\n", aliases: ["A"])
    code, check = @app.check([])
    assert_equal 1, code
    assert_equal ["modified"], check["changes"].map { |change| change["change_type"] }
    assert_equal 1, File.readlines(File.join(@scripts, "gate-count")).length

    code, review = @app.review(["A"])
    assert_equal 0, code
    packet = review["packet"]
    assert_equal "test-project", packet["project_id"]
    assert_equal ["Alpha"], packet["targets"]
    assert_equal ["Beta"], packet["required_context"].map { |item| item["title"] }
    assert_equal ["Gamma"], packet["advisory_context"].map { |item| item["title"] }
    assert packet.to_json.include?("untrusted-worldbook-content")
    refute packet.to_json.include?(@root)
    assert_equal packet["packet_hash"], Worldcheck::Util.hash(packet.reject { |key, _value| key == "packet_hash" })
  end

  def test_pass_receipt_advances_page_baseline_and_is_reused
    page("lore/Alpha.md", "Alpha", "# Alpha\nreviewed\n")
    _, review = @app.review([])
    code, recorded = @app.record(receipt(review["packet"], "pass"))
    assert_equal 0, code
    assert recorded["recorded"]
    code, status = @app.status
    assert_equal 0, code
    assert_empty status["changes"]
    assert_equal 1, status["baseline_sources"]["receipt"]
  end

  def test_packet_becomes_stale_before_receipt
    page("lore/Alpha.md", "Alpha", "# Alpha\nfirst\n")
    _, review = @app.review([])
    page("lore/Alpha.md", "Alpha", "# Alpha\nsecond\n")
    code, recorded = @app.record(receipt(review["packet"], "pass"))
    assert_equal 1, code
    assert_equal "stale", recorded["status"]
  end

  def test_required_budget_omission_forces_insufficient_evidence
    page("lore/Alpha.md", "Alpha", "# Alpha\n#{'x' * 10_000}\n")
    code, review = @app.review([], budget_chars: 2500)
    assert_equal 1, code
    assert_equal "insufficient-evidence", review["packet"]["reviewability"]
    assert_operator Worldcheck::Util.json(review["packet"]).length, :<=, 2500
  end

  def test_policy_change_requires_full_gate
    data = JSON.parse(File.read(File.join(@policies, "dependencies.json")))
    write_json("policies/dependencies.json", data.merge("graph_version" => 2))
    code, check = @app.check([])
    assert_equal 1, code
    assert_includes check["issues"].map { |item| item["code"] }, "full-gate-required"
    code, review = @app.review([])
    assert_equal 1, code
    assert_equal "full-gate-required", review["issues"].first["code"]
  end

  def test_rename_and_delete_are_page_level_changes
    FileUtils.mv(page_path("Alpha.md"), page_path("Renamed.md"))
    page("lore/Renamed.md", "Alpha", "# Alpha\nold\n", aliases: ["A"])
    File.delete(page_path("Beta.md"))
    _, check = @app.check([])
    kinds = check["changes"].map { |item| [item["title"], item["change_type"]] }
    assert_includes kinds, ["Alpha", "renamed"]
    assert_includes kinds, ["Beta", "deleted"]
  end

  def test_invalid_targets_and_duplicate_titles_are_rejected
    error = assert_raises(Worldcheck::Failure) { @app.review(["../Alpha"]) }
    assert_equal "target-invalid", error.code
    page("people/Alpha.md", "Alpha", "# duplicate\n")
    code, payload = @app.status
    assert_equal 1, code
    assert_includes payload["issues"].map { |item| item["code"] }, "title-duplicate"
  end

  def test_outside_symlinked_page_is_blocked
    outside = File.join(@tmp, "outside.md")
    File.write(outside, frontmatter("Outside") + "# outside\n")
    File.symlink(outside, File.join(@content, "Outside.md"))
    code, payload = @app.status
    assert_equal 1, code
    assert_includes payload["issues"].map { |item| item["code"] }, "path-outside-project"
  end

  def test_mixed_receipt_advances_hash_but_preserves_blocker
    page("lore/Alpha.md", "Alpha", "# Alpha\nquestionable\n")
    _, review = @app.review([])
    evidence = review["packet"]["changes"].first.slice("source_id", "content_hash", "anchor")
    finding = {"id" => "F-1", "severity" => "warning", "claim" => "存在歧义", "evidence" => [evidence], "rationale" => "需要作者判断", "suggested_action" => "明确边界"}
    code, = @app.record(receipt(review["packet"], "mixed", [finding]))
    assert_equal 1, code
    code, status = @app.status
    assert_equal 1, code
    assert_empty status["changes"]
    assert_equal "mixed", status["unresolved_receipts"].first["verdict"]
  end

  def test_receipt_cannot_cite_evidence_outside_packet
    page("lore/Alpha.md", "Alpha", "# Alpha\nchanged\n")
    _, review = @app.review([])
    evidence = {"source_id" => "outside-packet.md", "content_hash" => "sha256:#{'0' * 64}", "anchor" => "文首"}
    finding = {"id" => "F-1", "severity" => "error", "claim" => "冲突", "evidence" => [evidence], "rationale" => "外部证据", "suggested_action" => "修复"}
    error = assert_raises(Worldcheck::Failure) { @app.record(receipt(review["packet"], "fail", [finding])) }
    assert_equal "receipt-evidence-invalid", error.code
  end

  def test_config_rejects_empty_globs_absolute_and_parent_paths
    data = base_config.merge("page_globs" => [])
    write_json("bad.json", data)
    assert_equal "page-globs-invalid", assert_raises(Worldcheck::Failure) { Worldcheck::Project.load(File.join(@root, "bad.json")) }.code
    %w[/tmp/outside ../outside].each do |value|
      write_json("bad.json", base_config.merge("content_root" => value))
      assert_equal "path-invalid", assert_raises(Worldcheck::Failure) { Worldcheck::Project.load(File.join(@root, "bad.json")) }.code
    end
  end

  def test_config_rejects_policy_symlink_escape
    outside = File.join(@tmp, "outside.json")
    File.write(outside, "{}")
    File.symlink(outside, File.join(@policies, "outside.json"))
    write_json("bad.json", base_config.merge("policy_files" => ["policies/outside.json"]))
    assert_equal "path-outside-project", assert_raises(Worldcheck::Failure) { Worldcheck::Project.load(File.join(@root, "bad.json")) }.code
  end

  def test_optional_dependency_and_full_gate
    write_json("minimal.json", base_config.reject { |key, _| %w[dependency_file full_gate].include?(key) }.merge("project_id" => "minimal"))
    app = Worldcheck::App.new(Worldcheck::Project.load(File.join(@root, "minimal.json")), File.join(@tmp, "minimal-state"))
    code, result = app.check([], full: true)
    assert_equal 0, code
    assert_equal "not-configured", result["full_gate"]["status"]
    page("lore/Alpha.md", "Alpha", "# Alpha\nminimal\n")
    _, review = app.review([])
    assert_empty review["packet"]["required_context"]
  end

  def test_v1_state_is_rejected
    state_path = File.join(@state_root, "state.json")
    state = JSON.parse(File.read(state_path)).merge("schema_version" => 1)
    File.write(state_path, JSON.generate(state))
    error = assert_raises(Worldcheck::Failure) { @app.status }
    assert_equal "state-version-unsupported", error.code
  end

  private

  def base_config
    {
      "schema_version" => 1,
      "project_id" => "test-project",
      "content_root" => "worldbook",
      "page_globs" => ["**/*.md"],
      "policy_files" => %w[policies/canon-rules.json policies/design-principles.json policies/physics.json],
      "dependency_file" => "policies/dependencies.json",
      "full_gate" => {"argv" => ["sh", "scripts/gate.sh"]}
    }
  end

  def write_config
    write_json("worldcheck.json", base_config)
  end

  def config_path
    File.join(@root, "worldcheck.json")
  end

  def write_json(relative, value)
    path = File.join(@root, relative)
    FileUtils.mkdir_p(File.dirname(path))
    File.write(path, JSON.pretty_generate(value))
  end

  def page(relative, title, body, aliases: [])
    path = File.join(@content, relative)
    FileUtils.mkdir_p(File.dirname(path))
    File.write(path, frontmatter(title, aliases) + body)
  end

  def frontmatter(title, aliases = [])
    alias_yaml = aliases.empty? ? "" : "aliases:\n#{aliases.map { |item| "  - #{item}" }.join("\n")}\n"
    "---\ntype: concept\ntitle: #{title}\ncreated: 2026-08-19\nupdated: 2026-08-19\ntags: [test]\nstatus: developing\ncanon_status: canonical\nrelated: []\n#{alias_yaml}---\n"
  end

  def page_path(name)
    File.join(@content, "lore", name)
  end

  def receipt(packet, verdict, findings = [])
    {
      "receipt_version" => Worldcheck::RECEIPT_VERSION,
      "packet_hash" => packet["packet_hash"],
      "reviewer" => {"kind" => "llm", "provider" => "test", "model" => "fixture"},
      "verdict" => verdict,
      "findings" => findings,
      "omissions" => verdict == "insufficient-evidence" ? packet["omissions"] : [],
      "created_at" => Time.now.utc.iso8601
    }
  end
end
