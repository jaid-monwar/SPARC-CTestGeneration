from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, model_validator


class TestDesign(BaseModel):
    """Represents a high-level test design from Phase 1"""
    test_name: str = Field(..., description="Descriptive test name")
    test_description: str = Field(..., description="Detailed description of the test, including paths covered and expected outcomes")

    model_config = ConfigDict(extra="forbid")


class TestDesigns(BaseModel):
    """Collection of test designs for a function"""
    test_designs: List[TestDesign] = Field(..., description="List of test designs")

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# ENHANCED PHASE 1 TEST DESIGNER MODELS (Comprehensive Schema)
# ============================================================================

class TestMetadata(BaseModel):
    """Metadata about the test scenario"""
    test_id: str = Field(..., description="Unique test ID (e.g., INSERT_B1, DELETE_N2)")
    test_name: str = Field(..., description="Descriptive test name following pattern: test_<function>_<scenario>")
    test_category: str = Field(..., description="Category: boundary, normal_operation, edge_case, error_condition")
    description: str = Field(..., description="One-sentence description of what this test does")
    rationale: str = Field(..., description="Why this test matters and what bugs it catches")

    model_config = ConfigDict(extra="forbid")


class PathCoverage(BaseModel):
    """Information about which execution paths this test covers"""
    target_paths: List[str] = Field(..., description="Array of path IDs covered (e.g., ['P1', 'P3'])")
    path_conditions: List[str] = Field(..., description="Conditions that trigger these paths")
    expected_branches: List[str] = Field(..., description="Expected branch decisions during execution")

    model_config = ConfigDict(extra="forbid")


class SourceFunctionPrimary(BaseModel):
    """Primary function under test"""
    name: str = Field(..., description="Function name")
    signature: str = Field(..., description="Full function signature")
    extract_from: str = Field(..., description="Source file path")
    reason: str = Field(..., description="Why this function is needed")

    model_config = ConfigDict(extra="forbid")


class SourceFunctionDependency(BaseModel):
    """A dependency function called by the primary function"""
    name: str = Field(..., description="Dependency function name")
    signature: str = Field(..., description="Full function signature")
    extract_from: str = Field(..., description="Source file path")
    reason: str = Field(..., description="Why this dependency is needed")
    call_path: str = Field(..., description="Call chain (e.g., 'insert → newNode')")

    model_config = ConfigDict(extra="forbid")


class SourceFunctionsRequired(BaseModel):
    """All source functions needed for this test"""
    primary: SourceFunctionPrimary = Field(..., description="The main function under test")
    dependencies: List[SourceFunctionDependency] = Field(..., description="Functions called by primary")

    model_config = ConfigDict(extra="forbid")


class HelperFunctionSpec(BaseModel):
    """Specification for a helper function needed by the test"""
    name: str = Field(..., description="Helper function name")
    purpose: str = Field(..., description="What this helper does")
    from_pool: bool = Field(..., description="Whether from predefined pool")
    from_operation_map: Optional[bool] = Field(None, description="Whether from operation map")
    usage: str = Field(..., description="How/when this helper will be used")

    model_config = ConfigDict(extra="forbid")


class HelperFunctionsRequired(BaseModel):
    """All helper functions needed for this test"""
    assertions: List[HelperFunctionSpec] = Field(..., description="Assertion helpers for verification")
    utilities: List[HelperFunctionSpec] = Field(..., description="Utility helpers for setup/cleanup/generation")

    model_config = ConfigDict(extra="forbid")


class SetupRequirements(BaseModel):
    """Setup requirements before test execution"""
    data_structures: List[str] = Field(..., description="Data structures to create")
    preconditions: List[str] = Field(..., description="Conditions that must hold before test")
    initial_state: str = Field(..., description="High-level description of starting state")

    model_config = ConfigDict(extra="forbid")


class PrimaryFunctionArg(BaseModel):
    """Input argument for the primary function under test"""
    param_name: str = Field(..., description="Parameter name from function signature")
    param_type: str = Field(..., description="C type of parameter")
    test_value_semantic: str = Field(..., description="High-level description of test value")
    test_value_category: str = Field(..., description="Category: boundary, normal, edge, error")
    concrete_value: str = Field(..., description="Concrete test value to use")
    rationale: str = Field(..., description="Why this value was chosen")

    model_config = ConfigDict(extra="forbid")


class TestInputs(BaseModel):
    """Test inputs specification"""
    primary_function_args: List[PrimaryFunctionArg] = Field(..., description="Arguments for function under test")

    model_config = ConfigDict(extra="forbid")


class ReturnValueSpec(BaseModel):
    """Expected return value specification"""
    type: str = Field(..., description="C return type")
    description: str = Field(..., description="What should be returned")
    validation: str = Field(..., description="How to validate return value")

    model_config = ConfigDict(extra="forbid")


class SideEffect(BaseModel):
    """Observable side effect of the test"""
    effect: str = Field(..., description="What changes")
    observable_via: str = Field(..., description="How to observe this effect")

    model_config = ConfigDict(extra="forbid")


class ExpectedBehavior(BaseModel):
    """Expected behavior during test execution"""
    return_value: ReturnValueSpec = Field(..., description="Expected return value")
    side_effects: List[SideEffect] = Field(..., description="Observable side effects")
    state_changes: List[str] = Field(..., description="High-level state transitions")
    invariants_maintained: List[str] = Field(..., description="Invariants that must hold")

    model_config = ConfigDict(extra="forbid")


class AssertionRequired(BaseModel):
    """A single assertion required by the test"""
    assertion_id: str = Field(..., description="Sequential ID (A1, A2, A3, ...)")
    assertion_type: str = Field(..., description="Type: not_null, int_equal, pointer_equal, bst_property, null_pointer, etc.")
    target: str = Field(..., description="What to assert on")
    expected: str = Field(..., description="Expected value or condition")
    description: str = Field(..., description="What this assertion verifies")
    failure_meaning: str = Field(..., description="What failure indicates")

    model_config = ConfigDict(extra="forbid")


class CleanupRequirements(BaseModel):
    """Cleanup requirements after test execution"""
    memory_to_free: List[str] = Field(..., description="Memory resources to deallocate")
    resources_to_close: List[str] = Field(default_factory=list, description="Other resources to close")
    final_state: str = Field(..., description="Description of final clean state")
    cleanup_order: List[str] = Field(..., description="Ordered cleanup operations")

    model_config = ConfigDict(extra="forbid")


class TestDesignDetail(BaseModel):
    """Detailed design of the test logic"""
    setup_requirements: SetupRequirements = Field(..., description="Setup before test")
    test_inputs: TestInputs = Field(..., description="Input arguments specification")
    expected_behavior: ExpectedBehavior = Field(..., description="Expected behavior during execution")
    assertions_required: List[AssertionRequired] = Field(..., description="All assertions for this test")
    cleanup_requirements: CleanupRequirements = Field(..., description="Cleanup after test")

    model_config = ConfigDict(extra="forbid")


class VariableName(BaseModel):
    """A suggested variable name mapping"""
    semantic_name: str = Field(..., description="Semantic name (e.g., 'return_value', 'initial_tree')")
    c_variable_name: str = Field(..., description="Suggested C variable name (e.g., 'result', 'root')")

    model_config = ConfigDict(extra="forbid")


class ImplementationHints(BaseModel):
    """Hints to guide Phase 2 implementation"""
    variable_names: List[VariableName] = Field(..., description="Suggested variable name mappings")
    operation_sequence: List[str] = Field(..., description="High-level operation sequence")
    edge_cases_to_note: List[str] = Field(..., description="Specific edge cases to handle")

    model_config = ConfigDict(extra="forbid")


class EnhancedTestScenario(BaseModel):
    """Comprehensive test scenario from Phase 1 (Enhanced Format)"""
    test_metadata: TestMetadata = Field(..., description="Test metadata")
    path_coverage: PathCoverage = Field(..., description="Path coverage information")
    source_functions_required: SourceFunctionsRequired = Field(..., description="Source functions needed")
    helper_functions_required: HelperFunctionsRequired = Field(..., description="Helper functions needed")
    test_design: TestDesignDetail = Field(..., description="Detailed test design")
    implementation_hints: ImplementationHints = Field(..., description="Implementation guidance")

    model_config = ConfigDict(extra="forbid")


class TestSuiteMetadata(BaseModel):
    """Metadata about the entire test suite (or single-path test in per-path mode)"""
    function_under_test: str = Field(..., description="Name of function being tested")
    target_path: Optional[str] = Field(None, description="Target path ID for per-path generation (e.g., 'P1', 'P2')")
    source_file: Optional[str] = Field(None, description="Source file path")
    total_paths: Optional[int] = Field(None, description="Total number of execution paths")
    coverage_target: Optional[str] = Field(None, description="Coverage target (e.g., '100%')")

    model_config = ConfigDict(extra="forbid")


class PathCoverageInfo(BaseModel):
    """Coverage information for a single path"""
    path_id: str = Field(..., description="Path identifier (e.g., 'P1', 'P2', 'P3')")
    covered_by: List[str] = Field(..., description="Test IDs that cover this path")
    description: str = Field(..., description="What this path does")
    coverage_count: int = Field(..., description="Number of tests covering this path")

    model_config = ConfigDict(extra="forbid")


class CategoryDistribution(BaseModel):
    """Distribution of tests by category"""
    boundary: int = Field(0, description="Number of boundary tests")
    normal_operation: int = Field(0, description="Number of normal operation tests")
    edge_case: int = Field(0, description="Number of edge case tests")
    error_conditions: int = Field(0, description="Number of error condition tests")

    model_config = ConfigDict(extra="forbid")


class PriorityDistribution(BaseModel):
    """Distribution of tests by priority"""
    critical: int = Field(0, description="Number of critical priority tests")
    high: int = Field(0, description="Number of high priority tests")
    medium: int = Field(0, description="Number of medium priority tests")
    low: int = Field(0, description="Number of low priority tests")

    model_config = ConfigDict(extra="forbid")


class HelpersAggregate(BaseModel):
    """Aggregate of helpers from pool and operation map"""
    assertions: List[str] = Field(default_factory=list, description="Unique assertion helpers")
    utilities: List[str] = Field(default_factory=list, description="Unique utility helpers")

    model_config = ConfigDict(extra="forbid")


class RequiredHelpersAggregate(BaseModel):
    """Aggregate of all required helpers"""
    from_pool: HelpersAggregate = Field(..., description="Helpers from pool")
    from_operation_map: HelpersAggregate = Field(..., description="Helpers from operation map")

    model_config = ConfigDict(extra="forbid")


class EstimatedCoverage(BaseModel):
    """Estimated coverage metrics"""
    path_coverage_percent: str = Field(..., description="Path coverage (must be 100%)")
    expected_line_coverage_percent: str = Field(..., description="Expected line coverage range")
    branch_coverage_percent: str = Field(..., description="Branch coverage target")

    model_config = ConfigDict(extra="forbid")


class TestSuiteSummary(BaseModel):
    """Summary of the entire test suite (optional for per-path generation)"""
    total_tests_designed: Optional[int] = Field(None, description="Total number of test scenarios")
    path_coverage_analysis: Optional[List[PathCoverageInfo]] = Field(None, description="Coverage analysis for each execution path")
    category_distribution: Optional[CategoryDistribution] = Field(None, description="Distribution by category")
    required_helpers_aggregate: Optional[RequiredHelpersAggregate] = Field(None, description="Aggregate of all helpers")
    estimated_total_coverage: Optional[EstimatedCoverage] = Field(None, description="Estimated coverage metrics")
    integration_test_suggestions: Optional[List[str]] = Field(None, description="Suggestions for integration tests")

    model_config = ConfigDict(extra="forbid")


class EnhancedTestDesigns(BaseModel):
    """Complete test design output from Phase 1 (Enhanced Format)"""
    metadata: TestSuiteMetadata = Field(..., description="Test suite metadata")
    test_scenarios: List[EnhancedTestScenario] = Field(..., description="Detailed test scenarios")
    test_suite_summary: Optional[TestSuiteSummary] = Field(None, description="Test suite summary (optional for per-path generation)")

    model_config = ConfigDict(extra="forbid")


class Parameter(BaseModel):
    name: str = Field(..., description="Name of the function parameter")
    type: str = Field(..., description="C type of the parameter")

    model_config = ConfigDict(extra="forbid")


class FunctionModel(BaseModel):
    name: str = Field(..., description="Name of the helper function")
    description: str = Field(
        ..., description="Brief description of what the function does"
    )
    return_type: str = Field(..., description="C return type")
    parameters: List[Parameter] = Field(..., description="List of function parameters")
    code_block: str = Field(
        ..., description="Full C code definition for the helper function"
    )

    model_config = ConfigDict(extra="forbid")


class Path(BaseModel):
    path_id: int = Field(..., description="ID of the path")
    path: str = Field(..., description="Path of the source function")

    model_config = ConfigDict(extra="forbid")


class SourceFunction(BaseModel):
    name: str = Field(..., description="Name of the source function")
    paths: List[Path] = Field(..., description="List of paths for the source function")

    model_config = ConfigDict(extra="forbid")


class PlannedFunction(BaseModel):
    """Represents a function planned to be created with its dependencies"""

    name: str = Field(..., description="Name of the function to be created")
    calls: List[str] = Field(
        ..., description="List of all functions this function will call"
    )

    model_config = ConfigDict(extra="forbid")


class DependencyAnalysis(BaseModel):
    """Analysis section to ensure all dependencies are properly included

    Note: source_functions is NOT generated by GPT - it's always loaded from source_functions.json after generation
    """

    source_functions: Optional[List[SourceFunction]] = Field(
        None,
        description="All function names and paths from the source C code (loaded from source_functions.json)",
    )
    planned_created_functions: List[PlannedFunction] = Field(
        ..., description="Functions to be created with their dependencies"
    )
    required_from_pool: List[str] = Field(
        ..., description="All helper pool functions needed by created functions"
    )

    model_config = ConfigDict(extra="forbid")


class OperationMapSection(BaseModel):
    searched_from_pool: List[str] = Field(
        ..., description="List of helper function names found in DB"
    )
    created: List[FunctionModel] = Field(
        ..., description="List of newly proposed helper functions"
    )

    model_config = ConfigDict(extra="forbid")


class OperationMap(BaseModel):
    dependency_analysis: DependencyAnalysis = Field(
        ...,
        description="Analysis of dependencies to ensure all required functions are included",
    )
    assertion_operations: OperationMapSection = Field(
        ..., description="Operations related to assertions and validations"
    )
    utility_operations: OperationMapSection = Field(
        ..., description="Operations related to utility functions"
    )

    @model_validator(mode="after")
    def validate_dependencies(self):
        """Ensure all required helper pool functions are included in searched_from_pool sections"""
        required_functions = set(self.dependency_analysis.required_from_pool)

        included_functions = set()
        included_functions.update(self.assertion_operations.searched_from_pool)
        included_functions.update(self.utility_operations.searched_from_pool)

        missing_functions = required_functions - included_functions
        if missing_functions:
            raise ValueError(
                f"Missing required functions in searched_from_pool: {list(missing_functions)}"
            )

        return self

    model_config = ConfigDict(extra="forbid")


class VariableDeclaration(BaseModel):
    """Represents a variable declaration with name, type, and initial value"""

    name: str = Field(..., description="Variable name to declare")
    type: str = Field(
        ..., description="C type of the variable (like int, char*, struct node*)"
    )
    value: str = Field(..., description="Initial value for the variable")
    comment: Optional[str] = Field(
        None, description="Optional comment describing the variable's purpose"
    )

    model_config = ConfigDict(extra="forbid")


class InputParam(BaseModel):
    """Represents a single input parameter with name and usage specification"""

    name: str = Field(
        ...,
        description="Name of the parameter - MUST exactly match the parameter name defined in the operation map for this operation",
    )
    usage: str = Field(
        ...,
        description="How the parameter should be used in the function call (e.g., 'var_name', '&var_name', 'literal_value')",
    )

    model_config = ConfigDict(extra="forbid")


class OperationStep(BaseModel):
    op: str = Field(..., description="Operation name or function to call")
    variable_declarations: Optional[List[VariableDeclaration]] = Field(
        default=None, description="Variable declarations needed for this operation step"
    )
    input_params: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Input parameters as key-value pairs where key is parameter name and value specifies how it should be used (e.g., 'var_name', '&var_name', or concrete values like '5.0', 'NULL', 'tree')",
    )
    return_params: List[str] = Field(
        ..., description="List of return parameters expected from the operation"
    )

    model_config = ConfigDict(extra="forbid")


class TestScenario(BaseModel):
    test_name: str = Field(..., description="Name of the test scenario")
    setup: List[OperationStep] = Field(
        ..., description="Setup steps to prepare for the test"
    )
    steps: List[OperationStep] = Field(
        ..., description="Main steps of the test scenario"
    )
    cleanup: List[OperationStep] = Field(
        ..., description="Cleanup steps to revert changes after the test"
    )

    model_config = ConfigDict(extra="forbid")


class TestScenarios(BaseModel):
    test_scenarios: List[TestScenario] = Field(
        ..., description="List of test scenarios to be generated"
    )

    model_config = ConfigDict(extra="forbid")


class SeverityLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"


class CCodeIssue(BaseModel):
    """Represents a single compilation issue in C code"""

    line_number: int = Field(..., description="Line number where issue occurs")
    issue_type: str = Field(
        ..., description="Type of issue (INVALID_ARRAY_INIT, UNDEFINED_VARIABLE, etc.)"
    )
    description: str = Field(
        ..., description="Clear explanation of the compilation issue"
    )
    problematic_code: str = Field(..., description="The problematic code snippet")
    fixed_code: str = Field(..., description="The corrected code snippet")
    reason: str = Field(..., description="Explanation of why the fix is needed")
    file_source: Optional[str] = Field(
        None, description="Source file where issue occurs (unit_test or helpers)"
    )
    severity: Optional[SeverityLevel] = Field(
        SeverityLevel.ERROR, description="Severity level: error, warning, note"
    )

    model_config = ConfigDict(extra="forbid")


class CCodeValidationSummary(BaseModel):
    """Summary of C code validation results"""

    summary: str = Field(..., description="Summary of how errors were fixed")
    total_errors_fixed: int = Field(..., description="Total number of errors fixed")
    original_structure_preserved: bool = Field(
        ..., description="Whether original structure was preserved"
    )
    minimal_changes_applied: bool = Field(
        ..., description="Whether only minimal changes were applied"
    )

    model_config = ConfigDict(extra="forbid")


class CCodeValidationResult(BaseModel):
    """Result of validating generated C unit test code"""

    explanation: str = Field(
        ..., description="Explanation of the errors and how you fixed them"
    )
    validation_result: str = Field(..., description="PASS or FAIL")
    code_issues: List[CCodeIssue] = Field(
        ..., description="List of compilation issues found (errors and warnings)"
    )
    corrected_c_code: Optional[str] = Field(
        None, description="Full corrected unit test C code if issues found"
    )
    corrected_helpers_c_code: Optional[str] = Field(
        None, description="Full corrected helpers.c code if issues found"
    )
    validation_summary: CCodeValidationSummary = Field(
        ..., description="Summary of validation results"
    )

    model_config = ConfigDict(extra="forbid")
