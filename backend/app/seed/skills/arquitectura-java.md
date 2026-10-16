---
name: arquitectura-java
description: >
  Estándares de arquitectura Java de Nicolás Cano Leal: proyecto con build tool
  y layout estándar desde el commit inicial, modelado inmutable con records,
  contratos equals/hashCode/compareTo, jerarquía de excepciones de dominio,
  genéricos con PECS, streams sin efectos secundarios y JUnit 5. USAR SIEMPRE
  que se escriba, diseñe o refactorice código Java —clases de dominio,
  colecciones, excepciones, genéricos, streams, lambdas, concurrencia, tests o
  el `pom.xml`/`build.gradle`— aunque no se pida explícitamente "sigue mis
  estándares".
---

# Java — estándares de arquitectura de Nicolás Cano Leal

> Auditoría de origen: repo `ultimate-java` (curso Ultimate Java de Hola Mundo,
> 30 clases en `src/`, JDK 23, sin build tool ni tests). Cada bloque ❌ es
> código real de ese repo; el ✅ es la forma que debe tener cuando el código
> sale del cuaderno de curso y entra a un proyecto que alguien más va a
> mantener. **En un repo de apuntes, el ❌ es aceptable y didáctico** — la
> regla aplica a proyectos reales.

## Stack por defecto

Java 21 LTS (o 25 LTS; nunca una versión non-LTS en producción) · **Maven** por
defecto, Gradle solo si el proyecto ya lo usa · JUnit 5 + AssertJ · SLF4J +
Logback para logging · Checkstyle/SpotBugs en CI.

**Toolchain fijado en el build, no en el IDE.** Un `project-jdk-name="23"` en
`.idea/misc.xml` no compila en la máquina de nadie más ni en CI:

```xml
<properties>
  <maven.compiler.release>21</maven.compiler.release>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>
```

`release` (no `source`/`target`): garantiza que no se use API más nueva que la
versión objetivo. `sourceEncoding` explícito o los acentos de los `String` en
español se corrompen al compilar en Windows.

## 0. El repo nace con build tool, no con un `.iml`

Un proyecto cuyo único descriptor es `appjava.iml` + `src/` plano **no es
construible fuera de IntelliJ**: no puede declarar dependencias, no puede
correr tests, no puede tener CI. Antes de la primera clase de dominio:

```
pom.xml
src/main/java/io/nicolascano/<proyecto>/...
src/test/java/io/nicolascano/<proyecto>/...
src/main/resources/
```

- `src/main/java`, no `src/`. Es la convención que Maven/Gradle asumen sin
  configuración y la que todo lector de Java espera.
- `.gitignore` con `target/`, `build/`, `*.class`, `.idea/`, `*.iml`.
- **CI en el mismo commit inicial** (ver [[github-actions]]): `mvn -B verify`
  ya cubre compilar + tests. Un CI que solo lintea da falsa seguridad.

## 1. Paquetes: reverse-DNS, nunca el default package

```
❌ src/streams/Collector.java, src/colecciones/Lista.java, src/genericos/Lista.java
✅ io.nicolascano.app.pedidos.Pedido
```

Tres problemas concretos del layout plano:

- **Colisiones**: dos `Lista`, dos `Demo`, dos `User` en el mismo proyecto. Al
  necesitar ambas en un archivo hay que escribir el FQN completo.
- **Sombra de la JDK**: una clase `streams.Collector` impide importar
  `java.util.stream.Collector` desde su propio paquete. Nunca nombrar una
  clase igual que un tipo de `java.lang`, `java.util` o `java.util.stream`.
- **Default package**: `Main.java` sin `package` puede importar de paquetes
  nombrados, pero **nada puede importarlo a él** — queda inalcanzable para
  tests y para cualquier otro módulo. `Main` va en un paquete, siempre.

Organizar por **dominio** (`pedidos`, `usuarios`, `pagos`), no por tecnicismo
(`services`, `utils`, `helpers`). `utils` es donde va a morir el código que
nadie supo dónde poner.

## 2. Modelado de datos: `record` primero, mutabilidad justificada

```java
// ❌ campos públicos + constructores telescópicos + toString ausente
public class User {
    public int age;
    public String email;
    public Mandos mando;
    public User(int age) { this.age = age; }          // email y mando quedan null
    public User(int age, String email) { ... }
}

// ✅
public record User(int edad, String email, Mando mando) {
    public User {
        Objects.requireNonNull(email, "email");
        if (edad < 0) throw new EdadInvalidaException(edad);
    }
}
```

Qué se gana: `equals`/`hashCode`/`toString` correctos gratis (sin `toString`,
un `System.out.println` de una lista imprime `User@6d06d69c`), inmutabilidad,
imposibilidad de construir un objeto a medias, y validación en un solo lugar
(el constructor compacto).

- **Un solo constructor completo.** Los constructores telescópicos que dejan
  campos en `null` producen NPEs a cientos de líneas del origen. Si un campo
  es de verdad opcional, modelarlo como tal (`Optional<Mando> mando()` en el
  accesor, nunca un campo `Optional`).
- **Campos privados en las clases normales**, con getters solo donde hagan
  falta. Un campo público es un contrato que ya no se puede cambiar.
- **Jerarquías cerradas → `sealed`**: si el conjunto de subtipos es conocido,
  `sealed interface Pago permits Tarjeta, Transferencia` le permite al
  compilador verificar que el `switch` los cubre todos. Un `enum` cuando no
  llevan datos propios.

## 3. Los tres contratos que se rompen callados

**`equals`/`hashCode` van juntos, siempre.** Una clase sin ellos usa identidad
de referencia: `lista.contains(new User("Felipe", "f@x.io"))` da `false` aunque
el usuario esté ahí, y en un `HashSet` entran dos copias idénticas. Con
`record` no hay que escribirlos; en una clase normal, se generan y se
mantienen sincronizados con los campos.

**`compareTo` consistente con `equals`.** `EjemploComparable` compara por
nombre pero no define `equals`: en un `TreeSet` dos personas del mismo nombre
son "la misma" (el árbol usa `compareTo`) y en un `HashSet` son distintas. El
mismo objeto en dos colecciones da dos respuestas.

**Nunca restar para comparar** — desborda:

```java
❌ return this.tiempo - o.tiempo;              // Integer.MIN_VALUE rompe el orden
✅ return Integer.compare(this.tiempo, o.tiempo);
```

Y para comparadores, la forma declarativa antes que la clase suelta:

```java
❌ class EdadComparator implements Comparator<Persona> {         // NPE si edad es null
       public int compare(Persona a, Persona b) { return a.getEdad().compareTo(b.getEdad()); }
   }
✅ Comparator<Persona> porEdad = Comparator.comparingInt(Persona::edad)
                                           .thenComparing(Persona::nombre);
```

`comparingInt` evita el boxing y el NPE; `thenComparing` da un orden total y
estable sin escribir una sola rama.

## 4. Excepciones: dominio propio, causa encadenada, cero `printStackTrace`

```java
// ✅ raíz de negocio + subtipos con contexto
public sealed class DominioException extends RuntimeException permits EdadInvalidaException, ... {
    protected DominioException(String mensaje, Throwable causa) { super(mensaje, causa); }
}

public final class EdadInvalidaException extends DominioException {
    public EdadInvalidaException(int edad) {
        super("Edad inválida: %d, debe ser positiva".formatted(edad), null);
    }
}
```

Reglas:

- **Toda excepción propia expone `(String mensaje)` y `(String mensaje,
  Throwable causa)`.** Un `UserException(Exception e)` a secas hereda como
  mensaje el `toString()` de la causa y borra el contexto de quién falló.
- **Unchecked para errores de programación y de dominio; checked solo cuando
  quien llama puede hacer algo distinto** al recibirla (reintentar, pedir otro
  archivo). Una checked que todo el mundo re-lanza es ruido en cada firma.
- **No usar `catch` como control de flujo.** Dividir por cero se valida
  (`if (denominador == 0)`), no se atrapa con `catch (RuntimeException e)` —
  ese catch además se traga NPEs y bugs reales que no tienen nada que ver.
- **No devolver `-1` como código de error.** O se lanza, o se devuelve
  `Optional`/un tipo resultado. Un `-1` sobrevive tres capas y aparece en la
  base de datos.
- **`printStackTrace()` no es logging** — escribe en stderr, sin nivel, sin
  timestamp, sin contexto, y en producción no queda registrado en ningún lado.
  `logger.warn(...)` para lo esperable, `logger.error("...", e)` para lo que es
  un bug.
- `e.getStackTrace()` sin usar el valor devuelto es **una línea muerta**: no
  imprime nada. Si aparece, es un `printStackTrace()` mal recordado.
- **try-with-resources siempre** para cualquier `Closeable`; admite varios
  recursos separados por `;` y los cierra en orden inverso aunque el bloque
  lance.

## 5. Genéricos y colecciones propias

```java
// ❌
public class Lista<T> {
    private T[] data = (T[]) new Object[50];   // cast unchecked sin acotar, capacidad fija
    public Lista<T> add(T t) { data[length++] = t; return this; }  // revienta en el 51
}

// ✅
public class Lista<T> implements Iterable<T> {
    @SuppressWarnings("unchecked")             // acotado al campo: el array nunca se expone
    private T[] data = (T[]) new Object[CAPACIDAD_INICIAL];
    private int length;
    private int modCount;                      // para el fail-fast del iterador

    public Lista<T> add(T t) {
        if (length == data.length) data = Arrays.copyOf(data, data.length * 2);
        data[length++] = t;
        modCount++;
        return this;
    }
}
```

- **`@SuppressWarnings("unchecked")` en la declaración más pequeña posible**,
  con un comentario que explique por qué el cast es seguro (aquí: el array es
  privado y nunca se retorna, así que no hay heap pollution posible).
- **El iterador es una `private static final class`**, no una inner class: una
  inner class retiene una referencia implícita al objeto externo (fuga de
  memoria si el iterador sobrevive) — y guardar *además* un campo `lista` es
  duplicar esa referencia. Debe lanzar `NoSuchElementException` en `next()`
  agotado y `ConcurrentModificationException` si `modCount` cambió: un
  iterador que devuelve `null` en silencio esconde el bug.
- **PECS** (`Producer Extends, Consumer Super`): `Lista<? extends T>` para leer,
  `Lista<? super T>` para escribir. Los wildcards van en los **parámetros**,
  nunca en el tipo de retorno — obligan a quien llama a lidiar con capturas.
- **Declarar por la interfaz**: `List<X> l = new ArrayList<>()`, `Map`, `Set`,
  `Deque` — nunca `ArrayList<X> l = ...` en firmas públicas.
- **`Set.of(...)`/`List.of(...)` para colecciones fijas**, no
  `new HashSet<>(Arrays.asList(...))`. Son inmutables y no admiten `null`
  (lo cual es una ventaja: revientan donde está el bug).
- **La trampa de `List<Integer>.remove(3)`**: llama a `remove(int index)`, no a
  `remove(Object)` — borra el cuarto elemento, no el valor 3. Para borrar el
  valor: `remove(Integer.valueOf(3))`. En `Collection<Integer>` sí llama a
  `remove(Object)`, así que el mismo código cambia de significado según el tipo
  declarado.

## 6. Streams: pipeline sin efectos secundarios, un solo recorrido

- **`peek` es solo para depurar.** Loguear dentro de un `peek` deja un pipeline
  que hace cosas invisibles y que el runtime puede saltarse: con `count()`
  sobre un stream con tamaño conocido, Java **omite el pipeline entero** y el
  log nunca aparece. Si hay que loguear, `forEach` o un `map` explícito.
- **`Collectors.toMap` sin merge lanza `IllegalStateException`** ante la
  primera clave duplicada — y siempre hay duplicados algún día:
  ```java
  ❌ .collect(Collectors.toMap(u -> u.email, u -> u))
  ✅ .collect(Collectors.toMap(User::email, Function.identity(), (a, b) -> b))
  ```
- **Un stream se consume una vez.** `ages / users.stream().count()` recorre la
  colección dos veces y, con dos `int`, hace **división entera** (un promedio
  de 15.75 se reporta como 15):
  ```java
  ✅ double promedio = users.stream().mapToInt(User::edad).average().orElse(0);
  ```
- **Streams primitivos** (`IntStream`, `LongStream`, `DoubleStream`) para
  aritmética: sin boxing y con `sum()`/`average()`/`summaryStatistics()` ya
  hechos. `mapToInt` antes de reducir a mano.
- **Nunca `Optional.get()` a secas.** `orElse`, `orElseThrow(() -> ...)` o
  `ifPresent`. Un `.get()` sobre un `Optional` vacío es un
  `NoSuchElementException` sin contexto.
- **Referencias a método sobre lambdas** cuando no añaden nada:
  `.forEach(System.out::println)`, `Comparator.comparing(User::email)`.
- Los streams **infinitos** (`Stream.iterate`, `Stream.generate`) exigen una
  operación de corte (`limit`, `takeWhile`) **antes** de la terminal.
- `parallelStream()` solo con datos grandes, operaciones sin estado y tras
  medir. Por debajo de decenas de miles de elementos casi siempre pierde.

## 7. Lambdas e interfaces funcionales

- **`@FunctionalInterface` en toda interfaz pensada como lambda**: convierte un
  segundo método abstracto añadido por descuido en un error de compilación en
  vez de en una ruptura para todos los llamadores.
- **Reutilizar `java.util.function`** (`Predicate`, `Function`, `Consumer`,
  `Supplier`, `UnaryOperator`, `BinaryOperator`) antes de declarar una interfaz
  propia; declarar una propia solo cuando el **nombre del dominio** aporta
  (`Notificable.push` se lee mejor que `Consumer<String>`).
- **Componer en vez de anidar `if`**: `tieneArroba.and(minSeis).and(dominioValido)`,
  `notificar.andThen(guardar)`. Cada predicado se testea por separado.
- Las lambdas capturan variables **effectively final**: si hace falta mutar
  estado, el diseño está mal — acumular con `reduce`/`collect`.

## 8. Concurrencia

- **Inmutabilidad primero**: un `record` compartido entre hilos no necesita
  sincronización. La mayoría de los bugs de concurrencia se evitan no teniendo
  estado mutable compartido.
- **Nunca `new Thread()` a mano**: `ExecutorService` con un pool, o
  `Executors.newVirtualThreadPerTaskExecutor()` (Java 21+) para carga con
  mucho I/O bloqueante. Siempre dentro de try-with-resources o con `shutdown()`
  en un `finally`.
- `ConcurrentHashMap`/`CopyOnWriteArrayList` antes que `synchronized` a mano;
  `AtomicInteger` antes que `synchronized` para un contador.

## 9. Testing con JUnit 5

```xml
<dependencyManagement><dependencies>
  <dependency>
    <groupId>org.junit</groupId><artifactId>junit-bom</artifactId>
    <version>5.13.4</version><type>pom</type><scope>import</scope>
  </dependency>
</dependencies></dependencyManagement>
<dependencies>
  <dependency>
    <groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId><scope>test</scope>
  </dependency>
</dependencies>
```

El **BOM** alinea las versiones de todos los artefactos JUnit — nunca fijarlas
una por una. `maven-surefire-plugin` 3.5+ descubre y corre la plataforma sin
configuración extra.

- `@DisplayName` en español describiendo la **regla de negocio**, no el método:
  `"rechaza una edad negativa"`.
- `assertThrows(EdadInvalidaException.class, () -> new User(-1, ...))` para los
  caminos de error — y **verificar el mensaje/tipo**, no solo que lance algo.
- `@ParameterizedTest` + `@ValueSource`/`@CsvSource` para las tablas de casos
  límite, en vez de cuatro tests copiados.
- Lo primero y con más profundidad se testea la **lógica pura sin I/O**;
  cobertura objetivo ~83%, **100% en los caminos críticos**.
- Un `main` con llamadas comentadas **no es una suite de pruebas**: se pierde
  al primer commit y no falla en CI cuando algo se rompe.

## 10. Antipatrones de "código de curso" que no deben salir del cuaderno

- Clases con solo `public static void run()` y estado en `System.out`: son
  scripts, no diseño. En un proyecto real, el objeto tiene estado y devuelve
  valores; quien decide imprimir es la capa de presentación.
- **Bloques enteros comentados** como historial de versiones. Para eso está
  git; el código comentado se desincroniza y confunde al siguiente lector.
- `System.out.println` como mecanismo de salida de la lógica de negocio —
  imposible de testear y de redirigir. Devolver el valor, loguear aparte.

## Checklist antes de dar por terminado un módulo Java

- [ ] `mvn -B verify` limpio en checkout fresco (no "compila en mi IntelliJ").
- [ ] Ninguna clase en el default package; ningún nombre que sombree la JDK.
- [ ] Todo tipo de datos es `record` o tiene `equals`/`hashCode`/`toString`.
- [ ] `compareTo` con `Integer.compare`, consistente con `equals`.
- [ ] Cero `printStackTrace()`, cero `catch (Exception)` vacío, cero `-1` como
      código de error.
- [ ] Ningún `Optional.get()` ni `.toMap()` sin merge function.
- [ ] Tests JUnit 5 sobre los caminos críticos, no un `main` comentado.
- [ ] CI verde y badge en el README.

## Herramientas de apoyo

- **MCP `context7`** para documentación al día de **librerías** del ecosistema
  (JUnit, Spring Boot, Maven, Jackson): `resolve-library-id` → `query-docs`.
  Para el **lenguaje** en sí aporta poco (no es una librería); ahí manda la
  spec del JDK.
- **No hace falta un MCP de Java.** El análisis estático real se hace en el
  build, donde también corre en CI: `spotbugs-maven-plugin`,
  `maven-checkstyle-plugin`, `maven-enforcer-plugin` (prohibir dependencias
  duplicadas y versiones de JDK equivocadas).

## Ver también

[[arquitectura-software]] para el diseño (UML, SOLID, patrones) que este código
implementa · [[github-actions]] para el pipeline que corre `mvn verify` ·
[[docker]] para empaquetar el jar en una imagen multi-stage con JRE (no JDK) en
el runtime · [[python-backend]] para los mismos principios (excepciones de
dominio, capas, config fuera del código) expresados en Python.
