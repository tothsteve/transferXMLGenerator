/**
 * Commitlint Configuration
 *
 * Enforces conventional commit message format:
 * <type>(<scope>): <subject>
 *
 * Examples:
 *   feat(transfers): add NAV invoice selection modal
 *   fix(beneficiaries): fix account number validation
 *   docs(readme): update development setup
 *   chore(deps): update React to v19
 *
 * See: https://www.conventionalcommits.org/
 */

module.exports = {
  extends: ['@commitlint/config-conventional'],

  rules: {
    // Allowed types
    'type-enum': [
      2,
      'always',
      [
        'feat', // New feature
        'fix', // Bug fix
        'docs', // Documentation only changes
        'style', // Code style changes (formatting, missing semi-colons, etc)
        'refactor', // Code refactoring (neither fixes a bug nor adds a feature)
        'perf', // Performance improvement
        'test', // Adding or updating tests
        'chore', // Changes to build process or auxiliary tools
        'ci', // CI/CD related changes
        'revert', // Revert a previous commit
        'wip', // Work in progress (use sparingly)
      ],
    ],

    // Subject line rules
    'subject-case': [2, 'never', ['upper-case']], // Don't allow UPPER CASE
    'subject-empty': [2, 'never'], // Subject cannot be empty
    'subject-full-stop': [2, 'never', '.'], // No trailing period

    // Type rules
    'type-empty': [2, 'never'], // Type cannot be empty
    'type-case': [2, 'always', 'lower-case'], // Type must be lowercase

    // Scope rules (optional but recommended)
    'scope-empty': [1, 'never'], // Warn if scope is missing (not error)
    'scope-case': [2, 'always', 'lower-case'], // Scope must be lowercase

    // Header rules
    'header-max-length': [2, 'always', 100], // Max header length

    // Body and footer
    'body-leading-blank': [1, 'always'], // Blank line before body (warning)
    'footer-leading-blank': [1, 'always'], // Blank line before footer (warning)
  },
};
