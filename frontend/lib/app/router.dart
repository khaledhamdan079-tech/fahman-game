import 'package:fahman/features/authentication/presentation/sign_in_screen.dart';
import 'package:fahman/features/game/game_board_screen.dart';
import 'package:fahman/features/game/question_screen.dart';
import 'package:fahman/features/game/result_screen.dart';
import 'package:fahman/features/history/history_screen.dart';
import 'package:fahman/features/home/home_screen.dart';
import 'package:fahman/features/match_setup/presentation/category_selection_screen.dart';
import 'package:fahman/features/match_setup/presentation/team_setup_screen.dart';
import 'package:go_router/go_router.dart';

final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(path: '/', builder: (context, state) => const SignInScreen()),
    GoRoute(path: '/home', builder: (context, state) => const HomeScreen()),
    GoRoute(
      path: '/setup/categories',
      builder: (context, state) => const CategorySelectionScreen(),
    ),
    GoRoute(
      path: '/setup/teams',
      builder: (context, state) => const TeamSetupScreen(),
    ),
    GoRoute(
      path: '/game',
      builder: (context, state) => const GameBoardScreen(),
    ),
    GoRoute(
      path: '/question',
      builder: (context, state) => const QuestionScreen(),
    ),
    GoRoute(
      path: '/history',
      builder: (context, state) => const HistoryScreen(),
    ),
    GoRoute(path: '/result', builder: (context, state) => const ResultScreen()),
  ],
);
