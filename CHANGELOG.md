# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.4] - 2025-02-08

### Fixed
- Fix list -k error
- Fix scrolling error using vertical_overflow="visible"

## [0.2.3] - 2025-02-06

### Added
- Support deepseek-r1 reasoning content
- Add model, provider info

## [0.2.2] - 2025-02-06

### Fixed
- Prevent saving system message

## [0.2.0] - 2025-02-06

### Added
- Add MCP client support for integrating with Model Context Protocol servers
- Add cache_control for prompt caching

## [0.1.1] - 2025-02-05

### Fixed
- Fix fcntl compatible issue

### Added
- Support copy command when chat: use 0 for entire message, 1-n for specific code blocks
- Support OpenRouter indexed db file import
