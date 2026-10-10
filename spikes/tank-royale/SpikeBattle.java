import dev.robocode.tankroyale.runner.*;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.logging.*;

/** Fixed, trusted reference battle. Not an endpoint for participant submissions. */
public class SpikeBattle {
    static final Path OUT = Path.of("/tmp/evidence");
    static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r") + "\"";
    }
    public static void main(String[] args) throws Exception {
        Files.createDirectories(OUT.resolve("recordings"));
        Files.createDirectories(Path.of("/tmp/home"));
        Logger.getLogger("dev.robocode.tankroyale").setLevel(Level.WARNING);
        var watchdog = Executors.newSingleThreadScheduledExecutor();
        watchdog.schedule(() -> {
            System.err.println("FAIL: battle exceeded 180 second wall-clock limit");
            System.exit(124);
        }, 180, TimeUnit.SECONDS);
        final Instant start = Instant.now();
        final AtomicLong ticks = new AtomicLong();
        final List<Integer> ended = Collections.synchronizedList(new ArrayList<>());
        BattleResults result;
        try {
            Path root = Path.of("/opt/spike");
            Path bots = root.resolve(Files.readString(root.resolve("bots-root.txt")).trim());
            System.out.println("REAL_ENGINE 1.4.0 | Walls vs SpinBot | Classic | 5 rounds");
            try (var runner = BattleRunner.create(b -> {
                b.embeddedServer();
                b.suppressServerOutput();
                b.botConnectTimeout(Duration.ofSeconds(45));
                b.enableRecording(OUT.resolve("recordings"));
            })) {
                var setup = BattleSetup.classic(s -> s.setNumberOfRounds(5));
                try (var handle = runner.startBattleAsync(setup, List.of(
                        BotEntry.of(bots.resolve("Walls")), BotEntry.of(bots.resolve("SpinBot"))))) {
                    var owner = new Object();
                    handle.getOnTickEvent().on(owner, event -> ticks.incrementAndGet());
                    handle.getOnRoundEnded().on(owner, event -> {
                        ended.add(event.getRoundNumber());
                        System.out.printf("ROUND_ENDED round=%d turn=%d%n",
                                event.getRoundNumber(), event.getTurnNumber());
                    });
                    result = handle.awaitResults();
                }
            }
            var rows = new ArrayList<String>();
            for (var bot : result.getResults()) {
                rows.add("{\"name\":" + quote(bot.getName()) + ",\"version\":" + quote(bot.getVersion())
                    + ",\"rank\":" + bot.getRank() + ",\"totalScore\":" + bot.getTotalScore()
                    + ",\"survival\":" + bot.getSurvival() + ",\"bulletDamage\":" + bot.getBulletDamage()
                    + ",\"ramDamage\":" + bot.getRamDamage() + ",\"firstPlaces\":" + bot.getFirstPlaces()
                    + ",\"secondPlaces\":" + bot.getSecondPlaces() + "}");
                System.out.printf("RESULT rank=%d bot=%s score=%d firstPlaces=%d%n",
                        bot.getRank(), bot.getName(), bot.getTotalScore(), bot.getFirstPlaces());
            }
            String json = "{\"schema_version\":1,\"engine_version\":\"1.4.0\",\"source\":\"BattleResults\","
                    + "\"completed\":true,\"preset\":\"classic\",\"numberOfRounds\":" + result.getNumberOfRounds()
                    + ",\"observedTicks\":" + ticks.get() + ",\"observedRoundEnds\":" + ended
                    + ",\"duration_ms\":" + Duration.between(start, Instant.now()).toMillis()
                    + ",\"results\":[" + String.join(",", rows) + "]}\n";
            Files.writeString(OUT.resolve("results.json"), json, StandardOpenOption.CREATE_NEW);
            // Export before tmpfs disappears on container stop; stdout is the only output channel.
            try (var paths = Files.walk(OUT)) {
                for (var file : paths.filter(Files::isRegularFile).sorted().toList()) {
                    String relative = OUT.relativize(file).toString().replace('\\', '/');
                    String payload = Base64.getEncoder().encodeToString(Files.readAllBytes(file));
                    System.out.printf("ROBOCOPA_ARTIFACT %s %s%n", relative, payload);
                }
            }
            System.out.println("BATTLE_COMPLETED: results and official replay exported");
        } finally {
            watchdog.shutdownNow();
        }
    }
}
