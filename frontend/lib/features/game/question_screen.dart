import 'dart:async';

import 'package:audioplayers/audioplayers.dart';
import 'package:fahman/core/theme/app_theme.dart';
import 'package:fahman/features/match_setup/domain/match_snapshot.dart';
import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';

class QuestionScreen extends ConsumerStatefulWidget {
  const QuestionScreen({super.key});

  @override
  ConsumerState<QuestionScreen> createState() => _QuestionScreenState();
}

class _QuestionScreenState extends ConsumerState<QuestionScreen> {
  final AudioPlayer _audioPlayer = AudioPlayer();
  VideoPlayerController? _videoController;
  Timer? _timer;
  String? _mediaUrl;
  String? _mediaError;
  bool _mediaReadyReported = false;
  bool _preparingMedia = false;
  int? _frozenSeconds;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(
      const Duration(milliseconds: 250),
      (_) => mounted ? setState(() {}) : null,
    );
    WidgetsBinding.instance.addPostFrameCallback((_) => _prepareMedia());
  }

  @override
  void dispose() {
    _timer?.cancel();
    unawaited(_audioPlayer.dispose());
    unawaited(_videoController?.dispose());
    super.dispose();
  }

  Future<void> _prepareMedia() async {
    final question = ref
        .read(setupControllerProvider)
        .activeMatch
        ?.activeQuestion;
    if (question == null || question.type == 'text' || _preparingMedia) return;
    _preparingMedia = true;
    try {
      final playback = await ref
          .read(setupControllerProvider.notifier)
          .fetchPlayback();
      if (!mounted) return;
      if (playback == null) {
        await _reportMediaReady();
        return;
      }
      _mediaUrl = playback.url;
      if (question.type == 'audio') {
        await _audioPlayer.setSource(UrlSource(playback.url));
        await _reportMediaReady();
      } else if (question.type == 'video') {
        final controller = VideoPlayerController.networkUrl(
          Uri.parse(playback.url),
        );
        await controller.initialize();
        await controller.setLooping(false);
        _videoController = controller;
        await _reportMediaReady();
      } else {
        setState(() {});
      }
    } catch (_) {
      if (mounted) {
        setState(() => _mediaError = 'تعذر تحميل الوسائط. حاول مرة أخرى.');
      }
    } finally {
      _preparingMedia = false;
    }
  }

  Future<void> _reportMediaReady() async {
    if (_mediaReadyReported) return;
    _mediaReadyReported = true;
    await ref.read(setupControllerProvider.notifier).markMediaReady();
    if (mounted) setState(() {});
  }

  Future<void> _playMedia(ActiveQuestionSnapshot question) async {
    if (question.maxPlays != null && question.playCount >= question.maxPlays!) {
      _showMessage('انتهى عدد مرات التشغيل المتاحة.');
      return;
    }
    try {
      await ref.read(setupControllerProvider.notifier).recordMediaPlay();
      if (question.type == 'audio' && _mediaUrl != null) {
        await _audioPlayer.resume();
      } else if (question.type == 'video' && _videoController != null) {
        if (_videoController!.value.isPlaying) {
          await _videoController!.pause();
        } else {
          if (_videoController!.value.position >=
              _videoController!.value.duration) {
            await _videoController!.seekTo(Duration.zero);
          }
          await _videoController!.play();
        }
      }
      if (mounted) setState(() {});
    } catch (_) {
      _showMessage('لم نتمكن من تشغيل المقطع.');
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final setup = ref.watch(setupControllerProvider);
    final match = setup.activeMatch;
    final question = match?.activeQuestion;
    if (match == null || question == null) {
      return Scaffold(
        body: Center(
          child: FilledButton(
            onPressed: () => context.go('/game'),
            child: const Text('العودة للوحة'),
          ),
        ),
      );
    }
    final revealed = question.state == 'revealed';
    final remaining = revealed
        ? _frozenSeconds ?? 0
        : _remainingSeconds(question.deadline);
    return PopScope(
      canPop: false,
      child: Scaffold(
        backgroundColor: FahmanColors.cream,
        body: SafeArea(
          child: Stack(
            children: [
              Column(
                children: [
                  _QuestionHeader(match: match, remainingSeconds: remaining),
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
                      child: Center(
                        child: ConstrainedBox(
                          constraints: const BoxConstraints(maxWidth: 860),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              _QuestionMeta(question: question),
                              const SizedBox(height: 18),
                              if (question.type != 'text')
                                _MediaPanel(
                                  question: question,
                                  mediaUrl: _mediaUrl,
                                  error: _mediaError,
                                  videoController: _videoController,
                                  onImageReady: _reportMediaReady,
                                  onPlay: () => _playMedia(question),
                                  onRetry: _prepareMedia,
                                ),
                              if (question.type != 'text')
                                const SizedBox(height: 18),
                              _PromptCard(question: question),
                              const SizedBox(height: 18),
                              if (question.optionsVisible) ...[
                                _OptionsGrid(
                                  options: question.options,
                                  answer: revealed ? question.answer : null,
                                ),
                                const SizedBox(height: 18),
                              ] else if (!revealed) ...[
                                const _HiddenOptionsNotice(),
                                const SizedBox(height: 18),
                              ],
                              if (revealed) ...[
                                _AnswerCard(answer: question.answer!),
                                const SizedBox(height: 18),
                              ],
                              if (!revealed)
                                _QuestionActions(
                                  match: match,
                                  onLifeline: (type) => ref
                                      .read(setupControllerProvider.notifier)
                                      .useLifeline(type),
                                  onReveal: () async {
                                    _frozenSeconds = _remainingSeconds(
                                      question.deadline,
                                    );
                                    await _audioPlayer.stop();
                                    await _videoController?.pause();
                                    await ref
                                        .read(setupControllerProvider.notifier)
                                        .revealQuestion();
                                  },
                                )
                              else
                                _ScoringPanel(
                                  match: match,
                                  question: question,
                                  onScore: (team) async {
                                    final scored = await ref
                                        .read(setupControllerProvider.notifier)
                                        .scoreQuestion(team);
                                    if (scored && context.mounted) {
                                      final updated = ref
                                          .read(setupControllerProvider)
                                          .activeMatch;
                                      context.go(
                                        updated?.status == 'completed'
                                            ? '/result'
                                            : '/game',
                                      );
                                    }
                                  },
                                ),
                              if (setup.error != null) ...[
                                const SizedBox(height: 12),
                                Text(
                                  setup.error!,
                                  textAlign: TextAlign.center,
                                  style: const TextStyle(
                                    color: FahmanColors.coral,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              if (setup.isCreating)
                const Positioned.fill(
                  child: ColoredBox(
                    color: Color(0x550B1329),
                    child: Center(child: CircularProgressIndicator()),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  int? _remainingSeconds(DateTime? deadline) {
    if (deadline == null) return null;
    final milliseconds = deadline.difference(DateTime.now()).inMilliseconds;
    return (milliseconds / 1000).ceil().clamp(0, 999);
  }
}

class _QuestionHeader extends StatelessWidget {
  const _QuestionHeader({required this.match, required this.remainingSeconds});
  final MatchSnapshot match;
  final int? remainingSeconds;

  @override
  Widget build(BuildContext context) => Container(
    color: FahmanColors.midnight,
    padding: const EdgeInsets.fromLTRB(18, 12, 18, 14),
    child: Row(
      children: [
        _MiniScore(team: match.teams[0], active: match.currentTeam == 1),
        const Spacer(),
        Container(
          width: 76,
          height: 58,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: remainingSeconds == null
                ? FahmanColors.midnightSoft
                : remainingSeconds! <= 10
                ? FahmanColors.coral
                : FahmanColors.saffron,
            borderRadius: BorderRadius.circular(18),
          ),
          child: Text(
            remainingSeconds == null ? 'جاهز؟' : '$remainingSeconds',
            style: TextStyle(
              color: remainingSeconds == null || remainingSeconds! <= 10
                  ? Colors.white
                  : FahmanColors.midnight,
              fontSize: remainingSeconds == null ? 15 : 28,
              fontWeight: FontWeight.w900,
            ),
          ),
        ),
        const Spacer(),
        _MiniScore(team: match.teams[1], active: match.currentTeam == 2),
      ],
    ),
  );
}

class _MiniScore extends StatelessWidget {
  const _MiniScore({required this.team, required this.active});
  final MatchTeamSnapshot team;
  final bool active;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (active)
            const Padding(
              padding: EdgeInsetsDirectional.only(end: 6),
              child: Icon(Icons.circle, size: 9, color: FahmanColors.turquoise),
            ),
          Text(team.name, style: const TextStyle(color: Colors.white70)),
        ],
      ),
      Text(
        '${team.score}',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 22,
          fontWeight: FontWeight.w900,
        ),
      ),
    ],
  );
}

class _QuestionMeta extends StatelessWidget {
  const _QuestionMeta({required this.question});
  final ActiveQuestionSnapshot question;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: FahmanColors.saffron,
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          '${question.effectivePoints} نقطة',
          style: const TextStyle(fontWeight: FontWeight.w900),
        ),
      ),
      if (question.effectivePoints > question.points) ...[
        const SizedBox(width: 8),
        const Chip(
          avatar: Icon(Icons.exposure_plus_2_rounded, size: 18),
          label: Text('دبل'),
        ),
      ],
      const Spacer(),
      Text(
        _typeLabel(question.type),
        style: Theme.of(context).textTheme.bodyMedium,
      ),
    ],
  );

  static String _typeLabel(String type) => switch (type) {
    'image' => 'سؤال صورة',
    'audio' => 'سؤال صوتي',
    'video' => 'سؤال فيديو',
    _ => 'سؤال نصي',
  };
}

class _MediaPanel extends StatefulWidget {
  const _MediaPanel({
    required this.question,
    required this.mediaUrl,
    required this.error,
    required this.videoController,
    required this.onImageReady,
    required this.onPlay,
    required this.onRetry,
  });
  final ActiveQuestionSnapshot question;
  final String? mediaUrl;
  final String? error;
  final VideoPlayerController? videoController;
  final Future<void> Function() onImageReady;
  final VoidCallback onPlay;
  final VoidCallback onRetry;

  @override
  State<_MediaPanel> createState() => _MediaPanelState();
}

class _MediaPanelState extends State<_MediaPanel> {
  bool _imageReady = false;

  @override
  Widget build(BuildContext context) {
    if (widget.error != null) {
      return _MediaShell(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.cloud_off_rounded,
              size: 44,
              color: FahmanColors.coral,
            ),
            const SizedBox(height: 8),
            Text(widget.error!),
            TextButton(
              onPressed: widget.onRetry,
              child: const Text('إعادة المحاولة'),
            ),
          ],
        ),
      );
    }
    if (widget.question.type == 'image' && widget.mediaUrl != null) {
      return _MediaShell(
        child: Image.network(
          widget.mediaUrl!,
          fit: BoxFit.contain,
          frameBuilder: (context, child, frame, wasSynchronouslyLoaded) {
            if ((_imageReady || frame != null || wasSynchronouslyLoaded) &&
                !_imageReady) {
              _imageReady = true;
              WidgetsBinding.instance.addPostFrameCallback(
                (_) => widget.onImageReady(),
              );
            }
            return child;
          },
        ),
      );
    }
    final video = widget.videoController;
    if (widget.question.type == 'video' &&
        video != null &&
        video.value.isInitialized) {
      return _MediaShell(
        child: Stack(
          alignment: Alignment.center,
          children: [
            AspectRatio(
              aspectRatio: video.value.aspectRatio,
              child: VideoPlayer(video),
            ),
            _PlayButton(onTap: widget.onPlay, playing: video.value.isPlaying),
          ],
        ),
      );
    }
    if (widget.question.type == 'audio' &&
        (widget.mediaUrl != null || widget.question.mediaAssetId == null)) {
      return _MediaShell(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.graphic_eq_rounded,
              size: 70,
              color: FahmanColors.turquoise,
            ),
            const SizedBox(height: 8),
            _PlayButton(onTap: widget.onPlay),
            const SizedBox(height: 8),
            Text(
              'متبقي ${((widget.question.maxPlays ?? 2) - widget.question.playCount).clamp(0, 9)} تشغيل',
            ),
          ],
        ),
      );
    }
    if (widget.question.mediaAssetId == null) {
      return _MediaShell(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              widget.question.type == 'video'
                  ? Icons.movie_rounded
                  : Icons.image_rounded,
              size: 70,
              color: FahmanColors.purple,
            ),
            const SizedBox(height: 8),
            const Text('معاينة وسائط تجريبية'),
            if (widget.question.type == 'video') ...[
              const SizedBox(height: 8),
              _PlayButton(onTap: widget.onPlay),
            ],
          ],
        ),
      );
    }
    return const _MediaShell(child: Center(child: CircularProgressIndicator()));
  }
}

class _MediaShell extends StatelessWidget {
  const _MediaShell({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
    height: 260,
    clipBehavior: Clip.antiAlias,
    decoration: BoxDecoration(
      color: FahmanColors.midnight,
      borderRadius: BorderRadius.circular(26),
    ),
    child: child,
  );
}

class _PlayButton extends StatelessWidget {
  const _PlayButton({required this.onTap, this.playing = false});
  final VoidCallback onTap;
  final bool playing;

  @override
  Widget build(BuildContext context) => IconButton.filled(
    onPressed: onTap,
    style: IconButton.styleFrom(
      backgroundColor: FahmanColors.saffron,
      foregroundColor: FahmanColors.midnight,
      minimumSize: const Size.square(58),
    ),
    icon: Icon(
      playing ? Icons.pause_rounded : Icons.play_arrow_rounded,
      size: 34,
    ),
  );
}

class _PromptCard extends StatelessWidget {
  const _PromptCard({required this.question});
  final ActiveQuestionSnapshot question;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(24),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(25),
      border: Border.all(color: FahmanColors.line),
    ),
    child: Text(
      question.prompt,
      textAlign: TextAlign.center,
      style: Theme.of(context).textTheme.headlineMedium,
    ),
  );
}

class _OptionsGrid extends StatelessWidget {
  const _OptionsGrid({required this.options, required this.answer});
  final List<String> options;
  final String? answer;

  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 10,
    runSpacing: 10,
    children: [
      for (var index = 0; index < options.length; index++)
        Container(
          width: MediaQuery.sizeOf(context).width > 650
              ? 400
              : MediaQuery.sizeOf(context).width - 40,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: answer == options[index]
                ? FahmanColors.turquoise.withValues(alpha: 0.18)
                : Colors.white,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(
              color: answer == options[index]
                  ? FahmanColors.turquoise
                  : FahmanColors.line,
              width: answer == options[index] ? 2 : 1,
            ),
          ),
          child: Row(
            children: [
              CircleAvatar(
                radius: 15,
                backgroundColor: FahmanColors.midnight,
                foregroundColor: Colors.white,
                child: Text('${index + 1}'),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Text(
                  options[index],
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ),
            ],
          ),
        ),
    ],
  );
}

class _HiddenOptionsNotice extends StatelessWidget {
  const _HiddenOptionsNotice();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    decoration: BoxDecoration(
      color: FahmanColors.purple.withValues(alpha: 0.09),
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: FahmanColors.purple.withValues(alpha: 0.22)),
    ),
    child: const Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.visibility_off_rounded, color: FahmanColors.purple),
        SizedBox(width: 9),
        Flexible(child: Text('الخيارات مخفية — استخدم مساعدة إظهار الخيارات')),
      ],
    ),
  );
}

class _AnswerCard extends StatelessWidget {
  const _AnswerCard({required this.answer});
  final String answer;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(18),
    decoration: BoxDecoration(
      color: FahmanColors.turquoise.withValues(alpha: 0.16),
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: FahmanColors.turquoise, width: 2),
    ),
    child: Column(
      children: [
        const Text(
          'الإجابة الصحيحة',
          style: TextStyle(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 6),
        Text(
          answer,
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.headlineSmall,
        ),
      ],
    ),
  );
}

class _QuestionActions extends StatelessWidget {
  const _QuestionActions({
    required this.match,
    required this.onLifeline,
    required this.onReveal,
  });
  final MatchSnapshot match;
  final ValueChanged<String> onLifeline;
  final VoidCallback onReveal;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Wrap(
        alignment: WrapAlignment.center,
        spacing: 9,
        children: [
          _ActionLifeline(
            icon: Icons.list_alt_rounded,
            label: 'إظهار الخيارات',
            enabled: _available('show_options'),
            onTap: () => onLifeline('show_options'),
          ),
          _ActionLifeline(
            icon: Icons.block_rounded,
            label: 'حجب الخصم',
            enabled: _available('block_opponent'),
            onTap: () => onLifeline('block_opponent'),
          ),
        ],
      ),
      const SizedBox(height: 14),
      FilledButton.icon(
        onPressed: onReveal,
        style: FilledButton.styleFrom(backgroundColor: FahmanColors.coral),
        icon: const Icon(Icons.lightbulb_rounded),
        label: const Text('أظهر الإجابة'),
      ),
    ],
  );

  bool _available(String type) => match.lifelines.any(
    (item) =>
        item.teamNumber == match.currentTeam &&
        item.type == type &&
        item.state == 'available',
  );
}

class _ActionLifeline extends StatelessWidget {
  const _ActionLifeline({
    required this.icon,
    required this.label,
    required this.enabled,
    required this.onTap,
  });
  final IconData icon;
  final String label;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => OutlinedButton.icon(
    onPressed: enabled ? onTap : null,
    icon: Icon(icon),
    label: Text(enabled ? label : '$label ✓'),
  );
}

class _ScoringPanel extends StatelessWidget {
  const _ScoringPanel({
    required this.match,
    required this.question,
    required this.onScore,
  });
  final MatchSnapshot match;
  final ActiveQuestionSnapshot question;
  final ValueChanged<int?> onScore;

  @override
  Widget build(BuildContext context) {
    final blockedBy = match.lifelines
        .where(
          (item) =>
              item.type == 'block_opponent' &&
              item.matchQuestionId == question.id &&
              item.state == 'used',
        )
        .firstOrNull
        ?.teamNumber;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: FahmanColors.midnight,
        borderRadius: BorderRadius.circular(25),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'من صاحب الإجابة الصحيحة؟',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 19,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 14),
          for (final team in match.teams)
            Padding(
              padding: const EdgeInsets.only(bottom: 9),
              child: FilledButton(
                onPressed: blockedBy != null && blockedBy != team.number
                    ? null
                    : () => onScore(team.number),
                style: FilledButton.styleFrom(
                  backgroundColor: team.number == 1
                      ? FahmanColors.coral
                      : FahmanColors.purple,
                ),
                child: Text('${team.name}  +${question.effectivePoints}'),
              ),
            ),
          OutlinedButton(
            onPressed: () => onScore(null),
            style: OutlinedButton.styleFrom(foregroundColor: Colors.white),
            child: const Text('لا أحد'),
          ),
        ],
      ),
    );
  }
}
