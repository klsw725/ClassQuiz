// SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
//
// SPDX-License-Identifier: MPL-2.0

export enum ElementTypes {
	Text = 'TEXT', // eslint-disable-line no-unused-vars
	Headline = 'HEADLINE', // eslint-disable-line no-unused-vars
	Image = 'IMAGE', // eslint-disable-line no-unused-vars
	Rectangle = 'RECTANGLE', // eslint-disable-line no-unused-vars
	Circle = 'CIRCLE' // eslint-disable-line no-unused-vars
}

export interface QuizData {
	id?: string;
	title: string;
	description: string;
	quiz_id: string;
	questions: Question[];
	game_id: string;
	game_pin: string;
	started: boolean;
	cover_image?: string;
	background_color?: string;
	background_image?: string;
	time_based_scoring: boolean;
	likes: number;
	dislikes: number;
	plays: number;
	views: number;
}

export enum QuizQuestionType {
	ABCD = 'ABCD', // eslint-disable-line no-unused-vars
	RANGE = 'RANGE', // eslint-disable-line no-unused-vars
	VOTING = 'VOTING', // eslint-disable-line no-unused-vars
	SLIDE = 'SLIDE', // eslint-disable-line no-unused-vars
	TEXT = 'TEXT', // eslint-disable-line no-unused-vars
	MULTI_TEXT = 'MULTI_TEXT', // eslint-disable-line no-unused-vars
	ORDER = 'ORDER', // eslint-disable-line no-unused-vars
	CHECK = 'CHECK' // eslint-disable-line no-unused-vars
}

export interface RangeQuizAnswer {
	min: number;
	max: number;
	min_correct: number;
	max_correct: number;
}

export interface GeneralQuizAnswer {
	answer: string;
	right?: boolean;
	color?: string;
	emoji?: string;
	image?: string;
	case_sensitive?: boolean;
	id?: number;
	width?: number;
	height?: number;
}

export interface TextQuizAnswer extends GeneralQuizAnswer {
	answer: string;
	case_sensitive: boolean;
}

export interface OrderQuizAnswer extends GeneralQuizAnswer {
	answer: string;
	color?: string;
	id?: number;
	width?: number;
	height?: number;
}

export interface BaseQuestion {
	time: string;
	points: number;
	question: string;
	image?: string;
	hide_results?: boolean;
	ignore_whitespace?: boolean;
	multi_text_order_sensitive?: boolean;
}

export type Question =
	| (BaseQuestion & { type: QuizQuestionType.RANGE; answers: RangeQuizAnswer })
	| (BaseQuestion & { type: QuizQuestionType.SLIDE; answers: string })
	| (BaseQuestion & {
			type: QuizQuestionType.TEXT | QuizQuestionType.MULTI_TEXT;
			answers: TextQuizAnswer[];
	  })
	| (BaseQuestion & { type: QuizQuestionType.ORDER; answers: OrderQuizAnswer[] })
	| (BaseQuestion & {
			type: QuizQuestionType.ABCD | QuizQuestionType.CHECK;
			answers: Answer[];
	  })
	| (BaseQuestion & { type: QuizQuestionType.VOTING; answers: VotingAnswer[] })
	| (BaseQuestion & { type?: undefined; answers: Answer[] });

export type Answers = GeneralQuizAnswer[] | RangeQuizAnswer | string;

export interface Answer extends GeneralQuizAnswer {
	right: boolean;
	answer: string;
	color?: string;
	emoji?: string;
}

export interface VotingAnswer extends GeneralQuizAnswer {
	answer: string;
	image?: string;
	color?: string;
}

export interface EditorData {
	public: boolean;
	title: string;
	description: string;
	questions: Question[];
	cover_image?: string;
	background_color?: string;
	background_image?: string;
	time_based_scoring: boolean;
}

export interface PrivateImageData {
	id: string;
	uploaded_at: string;
	mime_type: string;
	hash?: string;
	size?: number;
	deleted_at?: string;
	alt_text?: string;
	filename?: string;
	thumbhash?: string;
	server?: string;
	imported: boolean;
	quizzes: { id: string }[];
	quiztivities: { id: string }[];
}
