# Implementation-evidence search strategies

For each requirement, search the codebase. Use multiple strategies — one search is
rarely enough to be confident.

**For backend requirements (ASP.NET Core / CQRS pattern):**
- Controllers: look for `[HttpGet]`, `[HttpPost]`, route attributes matching the endpoint
- Commands/Queries: look for MediatR `IRequest`, `ICommand`, `IQuery` handlers
- Models/Entities: look for EF Core entity classes, `DbSet<T>`, migration files
- Validators: FluentValidation classes covering the field/constraint

**For frontend requirements (DevExtreme / JS):**
- DevExtreme form items: `dataField`, `editorType`, component configs
- Grid/DataGrid columns: column definitions matching described fields
- API calls: `fetch`, `axios`, `$.ajax`, `dx.data.AspNet` URLs matching endpoints

**For UI specs:**
- CSS classes matching described layout or component
- HTML element structure matching described components

**For test coverage:**
- xUnit / NUnit test method names referencing the feature
- Test files in `Tests/` or `*.Tests/` directories

Run targeted searches — use function/class names from the design doc as search terms,
then branch out to synonyms and abbreviations if nothing turns up.
