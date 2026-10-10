import dev.robocode.tankroyale.runner.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.*;

/** Owner-only DSL experiment. Input comes exclusively from language.py's compiler. */
public class MobileBattle {
    static final Path OUT = Path.of("/tmp/evidence");
    static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }
    public static void main(String[] args) throws Exception {
        var watchdog = Executors.newSingleThreadScheduledExecutor();
        watchdog.schedule(() -> System.exit(124), 180, TimeUnit.SECONDS);
        try {
            byte[] request = System.in.readNBytes(98305);
            if (request.length > 98304) throw new IllegalArgumentException("Input limit");
            String[] parts = new String(request, StandardCharsets.US_ASCII).strip().split("\n", -1);
            if (parts.length != 2 || !parts[0].matches("[a-f0-9]{64}"))
                throw new IllegalArgumentException("Input protocol");
            String version = parts[0].substring(0, 12);
            byte[] source = Base64.getDecoder().decode(parts[1]);
            if (source.length > 65536) throw new IllegalArgumentException("Source limit");
            Files.createDirectories(OUT.resolve("recordings"));
            Files.createDirectories(Path.of("/tmp/home"));
            Path root = Path.of("/opt/spike");
            Path official = root.resolve(Files.readString(root.resolve("bots-root.txt")).trim());
            Path learner = Path.of("/tmp/mobile-bots/Aprendiz");
            Files.createDirectories(learner);
            Files.write(learner.resolve("Aprendiz.java"), source, StandardOpenOption.CREATE_NEW);
            Files.writeString(learner.resolve("Aprendiz.json"), "{\"name\":\"Aprendiz\",\"version\":"
                + quote(version) + ",\"authors\":[\"RoboCopa IFMA - experimento\"]}");
            Path launcher = learner.resolve("Aprendiz.sh");
            Files.writeString(launcher, "#!/bin/sh\nexec java -cp '" + official.resolve("lib/*") + "' Aprendiz.java\n");
            if (!launcher.toFile().setExecutable(true, false)) throw new IllegalStateException("Launcher permission");
            Logger.getLogger("dev.robocode.tankroyale").setLevel(Level.WARNING);
            Instant start = Instant.now();
            AtomicLong ticks = new AtomicLong();
            List<Integer> ended = Collections.synchronizedList(new ArrayList<>());
            BattleResults result;
            try (var runner = BattleRunner.create(b -> {
                b.embeddedServer(); b.suppressServerOutput();
                b.botConnectTimeout(Duration.ofSeconds(45));
                b.enableRecording(OUT.resolve("recordings"));
            })) {
                var setup = BattleSetup.classic(s -> s.setNumberOfRounds(3));
                try (var handle = runner.startBattleAsync(setup, List.of(
                        BotEntry.of(learner), BotEntry.of(official.resolve("Walls"))))) {
                    Object owner = new Object();
                    handle.getOnTickEvent().on(owner, e -> ticks.incrementAndGet());
                    handle.getOnRoundEnded().on(owner, e -> ended.add(e.getRoundNumber()));
                    result = handle.awaitResults();
                }
            }
            List<String> rows = new ArrayList<>();
            for (var bot : result.getResults()) {
                rows.add("{\"name\":" + quote(bot.getName()) + ",\"version\":" + quote(bot.getVersion())
                    + ",\"rank\":" + bot.getRank() + ",\"totalScore\":" + bot.getTotalScore()
                    + ",\"firstPlaces\":" + bot.getFirstPlaces() + ",\"secondPlaces\":" + bot.getSecondPlaces() + "}");
            }
            String json = "{\"schema_version\":1,\"engine_version\":\"1.4.0\",\"source\":\"BattleResults\","
                + "\"completed\":true,\"program_sha256\":" + quote(parts[0])
                + ",\"numberOfRounds\":" + result.getNumberOfRounds()
                + ",\"observedTicks\":" + ticks.get() + ",\"observedRoundEnds\":" + ended
                + ",\"duration_ms\":" + Duration.between(start, Instant.now()).toMillis()
                + ",\"results\":[" + String.join(",", rows) + "]}\n";
            Files.writeString(OUT.resolve("results.json"), json, StandardOpenOption.CREATE_NEW);
            try (var paths = Files.walk(OUT)) {
                for (var file : paths.filter(Files::isRegularFile).sorted().toList()) {
                    String relative = OUT.relativize(file).toString().replace('\\', '/');
                    System.out.printf("ROBOCOPA_ARTIFACT %s %s%n", relative,
                        Base64.getEncoder().encodeToString(Files.readAllBytes(file)));
                }
            }
            System.out.println("MOBILE_DSL_BATTLE_COMPLETED");
        } finally { watchdog.shutdownNow(); }
    }
}
