## ADDED Requirements

### Requirement: The delivery folder is declared by its name

A film SHALL declare its delivery folder as `delivery_folder`: the name of a folder, and no path of a host. A declaration that names the earlier key `documents_folder`, with or without the new key beside it, SHALL be refused when it loads, before any work, by a message that names `delivery_folder`.

#### Scenario: The earlier key

- **WHEN** a declaration names `documents_folder`
- **THEN** the engine refuses when it loads and names `delivery_folder`

#### Scenario: Both keys

- **WHEN** a declaration names `documents_folder` and `delivery_folder`
- **THEN** the engine refuses in the same way, and reads neither as the other
