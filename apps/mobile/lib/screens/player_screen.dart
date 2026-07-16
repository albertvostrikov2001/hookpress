import 'package:flutter/material.dart';
import 'package:just_audio/just_audio.dart';
import 'package:provider/provider.dart';

import '../l10n/app_localizations.dart';
import '../services/auth_service.dart';

class PlayerScreen extends StatefulWidget {
  const PlayerScreen({super.key});

  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> {
  final _player = AudioPlayer();
  bool _loading = true;
  String? _error;
  String? _trackTitle;
  String? _sourceLabel;

  @override
  void initState() {
    super.initState();
    _loadAudio();
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  Future<void> _loadAudio() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = context.read<AuthService>().api;
      final projects = await api.listStudioProjects();
      if (projects.isEmpty) {
        setState(() {
          _loading = false;
          _error = 'no_projects';
        });
        return;
      }
      final project = projects.first;
      _trackTitle = project['title']?.toString();
      final presigned = await api.getAudioPresignedUrl(project['id'] as String);
      if (presigned == null || presigned['url'] == null) {
        setState(() {
          _loading = false;
          _error = 'no_audio';
        });
        return;
      }
      await _player.setUrl(presigned['url'] as String);
      _sourceLabel = presigned['media_asset_id']?.toString();
      if (mounted) setState(() => _loading = false);
    } catch (_) {
      if (mounted) {
        setState(() {
          _loading = false;
          _error = 'load_failed';
        });
      }
    }
  }

  String _formatTime(Duration d) {
    final total = d.inSeconds;
    final m = total ~/ 60;
    final s = total % 60;
    return '${m.toString().padLeft(2, '0')}:${s.toString().padLeft(2, '0')}';
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(l10n.playerStub),
            const SizedBox(height: 12),
            FilledButton(onPressed: _loadAudio, child: Text(l10n.retryButton)),
          ],
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const Spacer(),
          Container(
            width: 200,
            height: 200,
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(
              Icons.music_note,
              size: 80,
              color: theme.colorScheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(height: 24),
          Text(
            _trackTitle ?? l10n.playerTrackTitle,
            style: theme.textTheme.titleLarge,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            l10n.playerArtist,
            style: theme.textTheme.bodyMedium,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 32),
          StreamBuilder<Duration>(
            stream: _player.positionStream,
            builder: (context, snap) {
              final position = snap.data ?? Duration.zero;
              final duration = _player.duration ?? Duration.zero;
              final max = duration.inMilliseconds > 0 ? duration.inSeconds.toDouble() : 1.0;
              return Column(
                children: [
                  Slider(
                    value: position.inSeconds.clamp(0, max.toInt()).toDouble(),
                    max: max,
                    onChanged: (v) => _player.seek(Duration(seconds: v.round())),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(_formatTime(position)),
                        Text(_formatTime(duration)),
                      ],
                    ),
                  ),
                ],
              );
            },
          ),
          const SizedBox(height: 16),
          StreamBuilder<PlayerState>(
            stream: _player.playerStateStream,
            builder: (context, snap) {
              final playing = snap.data?.playing ?? false;
              return Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  IconButton(
                    iconSize: 36,
                    icon: const Icon(Icons.skip_previous),
                    onPressed: () => _player.seek(Duration.zero),
                  ),
                  IconButton(
                    iconSize: 64,
                    icon: Icon(playing ? Icons.pause_circle : Icons.play_circle),
                    onPressed: () {
                      if (playing) {
                        _player.pause();
                      } else {
                        _player.play();
                      }
                    },
                  ),
                  IconButton(
                    iconSize: 36,
                    icon: const Icon(Icons.skip_next),
                    onPressed: () {
                      final d = _player.duration;
                      if (d != null) _player.seek(d);
                    },
                  ),
                ],
              );
            },
          ),
          const Spacer(),
          if (_sourceLabel != null)
            Text(
              l10n.playerSourceLabel(_sourceLabel!),
              style: theme.textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
        ],
      ),
    );
  }
}
