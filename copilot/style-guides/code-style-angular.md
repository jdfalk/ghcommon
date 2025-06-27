<!-- file: copilot/code-style-angular.md -->
<!-- version: 1.0.0 -->
<!-- guid: 8f7e6d5c-4b3a-2c1d-0e9f-8a7b6c5d4e3f -->

# Angular Coding Style Guide

This guide is based on the [Angular Style Guide](https://angular.io/guide/styleguide) and provides comprehensive guidelines for writing clean, consistent Angular applications.

## Style Vocabulary

### Guideline Strength

- **Do**: Should always be followed (with rare exceptions)
- **Consider**: Generally should be followed unless there's a good reason to deviate
- **Avoid**: Should almost never be done

## Naming Conventions

### General Naming Guidelines

- **Use consistent names** for all symbols
- **Follow pattern**: `feature.type.ts` (feature then type)
- **Use descriptive names** that clearly convey intent

### File Naming

- **Separate with dots and dashes**: Use dashes for descriptive words, dots for type separation
- **Type naming**: `.service`, `.component`, `.pipe`, `.module`, `.directive`
- **Examples**:
  - `hero-list.component.ts`
  - `user-profile.service.ts`
  - `validation.directive.ts`

### Symbol and Class Naming

- **Classes**: `UpperCamelCase` (PascalCase)
- **Match symbol to filename**: Symbol name should match file name
- **Add conventional suffixes**: `Component`, `Directive`, `Module`, `Pipe`, `Service`

| Symbol Type | Class Name            | File Name                 |
| ----------- | --------------------- | ------------------------- |
| Component   | `AppComponent`        | `app.component.ts`        |
| Service     | `HeroService`         | `hero.service.ts`         |
| Directive   | `ValidationDirective` | `validation.directive.ts` |
| Pipe        | `InitCapsPipe`        | `init-caps.pipe.ts`       |
| Module      | `AppModule`           | `app.module.ts`           |

### Component Selectors

- **Use kebab-case** for element selectors: `toh-hero-button`
- **Use custom prefix** to prevent collisions: `toh-`, `admin-`
- **Be consistent** with prefix across application

### Directive Selectors

- **Use camelCase** for attribute directives: `tohHighlight`
- **Use custom prefix** to prevent collisions
- **Don't use `ng` prefix** (reserved for Angular)

### Service Names

- **Suffix with `Service`**: `HeroDataService`, `CreditService`
- **Exception for obvious services**: `Logger` (not `LoggerService`)
- **Be consistent** within project

### Test File Naming

- **Unit tests**: Same name as component + `.spec` suffix
- **E2E tests**: Feature name + `.e2e-spec` suffix

## Application Structure (LIFT Principles)

### L - Locate Code Quickly

- **Organize intuitively**: Related files should be near each other
- **Use descriptive folder structure**: Clear hierarchy that makes sense
- **Keep related files together**: Component files in same directory

### I - Identify Code at a Glance

- **Descriptive file names**: Instantly know what file contains
- **One component per file**: Avoid mixing multiple components
- **Clear content organization**: File contents should match expectations

### F - Flat Structure

- **Keep flat as long as possible**: Avoid deep nesting
- **Create subfolders at 7+ files**: When folder gets too crowded
- **Balance structure and simplicity**: Don't over-organize small projects

### T - Try to be DRY (Don't Repeat Yourself)

- **Avoid redundancy**: But don't sacrifice readability
- **Be pragmatic**: Sometimes repetition is clearer than abstraction

## Folder Structure

### Feature-Based Organization

```
src/
  app/
    core/
      exception.service.ts|spec.ts
      user-profile.service.ts|spec.ts
    heroes/
      hero/
        hero.component.ts|html|css|spec.ts
      hero-list/
        hero-list.component.ts|html|css|spec.ts
      shared/
        hero.model.ts
        hero.service.ts|spec.ts
      heroes.component.ts|html|css|spec.ts
      heroes.module.ts
      heroes-routing.module.ts
    shared/
      shared.module.ts
      init-caps.pipe.ts|spec.ts
      filter-text.component.ts|spec.ts
    app.component.ts|html|css|spec.ts
    app.module.ts
    app-routing.module.ts
```

### Module Organization

- **Root module**: `AppModule` in `/src/app`
- **Feature modules**: One per distinct feature area
- **Shared module**: For commonly used components/services
- **Core module**: For singleton services (import once in AppModule)

## Component Guidelines

### Single Responsibility

- **One component per file**: Maximum 400 lines of code
- **Small functions**: Limit to 75 lines when possible
- **Focused purpose**: Each component should do one thing well

### Template and Style Separation

- **Extract templates >3 lines**: Use separate `.html` files
- **Extract styles >3 lines**: Use separate `.css` files
- **Use relative URLs**: `./component.html`, `./component.css`

### Input/Output Properties

- **Use decorators**: `@Input()` and `@Output()` instead of metadata
- **Place on same line**: When it improves readability
- **Avoid aliasing**: Unless serving important purpose
- **Don't prefix outputs with `on`**: Use `saved` not `onSaved`

### Component Structure

```typescript
@Component({
  selector: "toh-hero-list",
  templateUrl: "./hero-list.component.html",
  styleUrls: ["./hero-list.component.css"],
})
export class HeroListComponent implements OnInit {
  // Public properties first
  @Input() heroes: Hero[] = [];
  @Output() heroSelected = new EventEmitter<Hero>();

  // Private properties
  private selectedHero?: Hero;

  // Constructor
  constructor(private heroService: HeroService) {}

  // Lifecycle hooks
  ngOnInit(): void {
    this.loadHeroes();
  }

  // Public methods
  selectHero(hero: Hero): void {
    this.selectedHero = hero;
    this.heroSelected.emit(hero);
  }

  // Private methods
  private loadHeroes(): void {
    this.heroService.getHeroes().subscribe((heroes) => (this.heroes = heroes));
  }
}
```

### Member Sequence

1. **Public properties** (including `@Input()` and `@Output()`)
2. **Private properties**
3. **Constructor**
4. **Lifecycle hooks** (in order: OnInit, OnChanges, etc.)
5. **Public methods**
6. **Private methods**

### Component Logic

- **Delegate complex logic to services**: Keep components focused on presentation
- **Put presentation logic in component class**: Not in template
- **Initialize inputs**: Provide defaults or mark as optional with `?`

## Directive Guidelines

### Purpose and Usage

- **Use for element enhancement**: When you need presentation logic without template
- **Attribute directives**: For behavior modification
- **Structural directives**: For DOM manipulation

### Host Bindings

- **Prefer decorators**: Use `@HostListener` and `@HostBinding` over `host` metadata
- **Be consistent**: Choose one approach and stick with it

```typescript
@Directive({
  selector: "[tohHighlight]",
})
export class HighlightDirective {
  @HostBinding("class.highlighted") isHighlighted = false;

  @HostListener("mouseenter") onMouseEnter() {
    this.isHighlighted = true;
  }

  @HostListener("mouseleave") onMouseLeave() {
    this.isHighlighted = false;
  }
}
```

## Service Guidelines

### Service Design

- **Single responsibility**: Each service should have one clear purpose
- **Use as singletons**: Share data and functionality across components
- **Provide at root level**: Use `providedIn: 'root'` for app-wide services

### Dependency Injection

- **Use `@Injectable()` decorator**: For all services
- **Constructor injection**: Declare dependencies in constructor
- **Type-based tokens**: Prefer over string tokens when possible

```typescript
@Injectable({
  providedIn: "root",
})
export class HeroService {
  constructor(private http: HttpClient) {}

  getHeroes(): Observable<Hero[]> {
    return this.http.get<Hero[]>("api/heroes");
  }
}
```

### Data Services

- **Encapsulate data operations**: Handle HTTP calls, local storage, caching
- **Return observables**: For asynchronous operations
- **Handle errors**: Implement proper error handling and retry logic

## Module Guidelines

### Module Types

- **App Module**: Root module that bootstraps the application
- **Feature Modules**: Organize related functionality
- **Shared Modules**: Export common components, directives, pipes
- **Core Module**: Singleton services and app-wide components

### Shared Module Pattern

```typescript
@NgModule({
  imports: [CommonModule, FormsModule],
  declarations: [FilterTextComponent, InitCapsPipe],
  exports: [CommonModule, FormsModule, FilterTextComponent, InitCapsPipe],
})
export class SharedModule {}
```

### Lazy Loading

- **Feature modules**: Design for lazy loading when appropriate
- **Avoid direct imports**: Don't import lazy-loaded modules directly
- **Route-based loading**: Use Angular Router for lazy loading

## Best Practices

### Performance

- **Avoid filtering/sorting in pipes**: Pre-compute in components or services
- **OnPush change detection**: For performance-critical components
- **Track by functions**: For `*ngFor` with large lists

### Testing

- **Test file naming**: Component name + `.spec.ts`
- **Mock dependencies**: Use dependency injection for testability
- **Component testing**: Test component logic separately from template

### Code Organization

- **Consistent imports**: Group and order imports logically
- **Export barrel**: Use index files for clean imports
- **Avoid deep nesting**: Keep folder structure as flat as reasonable

### TypeScript Guidelines

- **Strict mode**: Enable strict TypeScript compiler options
- **Type everything**: Avoid `any` type when possible
- **Interface segregation**: Create focused interfaces
- **Implement lifecycle interfaces**: For type safety and documentation

## Example Component Template

```typescript
import { Component, Input, Output, EventEmitter, OnInit } from "@angular/core";
import { Hero } from "../shared/hero.model";
import { HeroService } from "../shared/hero.service";

@Component({
  selector: "toh-hero-detail",
  templateUrl: "./hero-detail.component.html",
  styleUrls: ["./hero-detail.component.css"],
})
export class HeroDetailComponent implements OnInit {
  @Input() hero?: Hero;
  @Output() heroSaved = new EventEmitter<Hero>();
  @Output() heroDeleted = new EventEmitter<Hero>();

  isEditing = false;

  constructor(private heroService: HeroService) {}

  ngOnInit(): void {
    // Initialization logic
  }

  editHero(): void {
    this.isEditing = true;
  }

  saveHero(): void {
    if (this.hero) {
      this.heroService.updateHero(this.hero).subscribe((hero) => {
        this.isEditing = false;
        this.heroSaved.emit(hero);
      });
    }
  }

  deleteHero(): void {
    if (this.hero) {
      this.heroService.deleteHero(this.hero.id).subscribe(() => {
        this.heroDeleted.emit(this.hero);
      });
    }
  }
}
```

This style guide ensures consistency, maintainability, and scalability in Angular applications while following Google's recommended practices and Angular team guidelines.
